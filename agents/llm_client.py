"""
Real LLM Client & Execution Audit Logger for the Autonomous E-commerce Trust Agent.
Supports Google Gemini (gemini-2.5-flash / gemini-2.0-flash) and Groq (llama-3.3-70b-versatile).
No fake model names and no silent fallback to mock/demo outputs.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        pkg_root = Path(__file__).resolve().parent.parent
        load_dotenv(pkg_root / ".env")
        load_dotenv()
        return
    except ImportError:
        pass

    for candidate in (Path(__file__).resolve().parent.parent / ".env", Path(".env")):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


_load_env()

logger = logging.getLogger("TrustAgentLLM")
logger.setLevel(logging.INFO)


class LLMError(RuntimeError):
    """Raised when an LLM API key is missing or a live LLM request fails."""


class AgentAuditLogger:
    """Collects granular per-agent execution logs for transparent operator auditing."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logs = []
        return cls._instance

    def log_event(self, agent_id: int, agent_name: str, event_type: str, data: Dict[str, Any]) -> None:
        self.logs.append(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent_id": agent_id,
                "agent_name": agent_name,
                "event_type": event_type,
                "data": data,
            }
        )

    def get_logs(self) -> List[Dict[str, Any]]:
        return list(self.logs)

    def clear(self) -> None:
        self.logs.clear()


audit_logger = AgentAuditLogger()


class TrustAgentLLMClient:
    """Unified live LLM client for Google Gemini and Groq."""

    def __init__(
        self,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.provider = provider.strip().lower()
        if self.provider not in ("gemini", "groq"):
            raise ValueError("Provider must be 'gemini' or 'groq'.")

        if api_key is not None:
            self.api_key = api_key.strip()
        elif self.provider == "gemini":
            self.api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        else:
            self.api_key = (os.getenv("GROQ_API_KEY") or "").strip()

        if model and model.strip():
            self.model = model.strip()
        elif self.provider == "gemini":
            self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        else:
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _require_key(self) -> None:
        if not self.is_available():
            env_var = "GEMINI_API_KEY" if self.provider == "gemini" else "GROQ_API_KEY"
            raise LLMError(
                f"No API key configured for {self.provider.title()}. "
                f"Enter your API key in the sidebar or set {env_var} in your .env file."
            )

    @staticmethod
    def parse_json(raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                return json.loads(match.group(0))
            raise LLMError(f"LLM returned non-JSON output: {raw_text[:280]}")

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        json_mode: bool = False,
        temperature: float = 0.1,
        timeout: int = 35,
    ) -> Tuple[str, str, float]:
        """Executes a live LLM call. Returns (response_text, model_used, latency_ms)."""
        self._require_key()
        if self.provider == "gemini":
            return self._call_gemini(prompt, system_instruction, json_mode, temperature, timeout)
        return self._call_groq(prompt, system_instruction, json_mode, temperature, timeout)

    def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.1,
        timeout: int = 35,
    ) -> Tuple[Dict[str, Any], str, float]:
        text, model_used, latency_ms = self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=True,
            temperature=temperature,
            timeout=timeout,
        )
        return self.parse_json(text), model_used, latency_ms

    def _call_gemini(
        self,
        prompt: str,
        system_instruction: str,
        json_mode: bool,
        temperature: float,
        timeout: int,
    ) -> Tuple[str, str, float]:
        t0 = time.perf_counter()
        gen_cfg: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": 2048,
        }
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_cfg,
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        models_to_try = [self.model]
        for candidate in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error = ""
        for cur_model in models_to_try:
            for attempt in range(2):
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{cur_model}:generateContent?key={self.api_key}"
                )
                try:
                    resp = requests.post(url, json=payload, timeout=timeout)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
                        return text, f"gemini:{cur_model}", elapsed_ms
                    elif resp.status_code in (503, 429):
                        last_error = f"Gemini {cur_model} returned {resp.status_code} (Service Unavailable / Busy). Retrying..."
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    else:
                        raise LLMError(f"Gemini API error ({resp.status_code}): {resp.text[:300]}")
                except requests.RequestException as exc:
                    last_error = str(exc)
                    time.sleep(0.5)
                    continue

        raise LLMError(f"Gemini API temporarily unavailable (503 / network error): {last_error}")

    def _call_groq(
        self,
        prompt: str,
        system_instruction: str,
        json_mode: bool,
        temperature: float,
        timeout: int,
    ) -> Tuple[str, str, float]:
        t0 = time.perf_counter()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            raise LLMError(f"Network error calling Groq API ({self.model}): {exc}") from exc

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        if resp.status_code != 200:
            raise LLMError(f"Groq API error ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        try:
            text = (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Groq response format: {data}") from exc

        return text, f"groq:{self.model}", elapsed_ms
