"""
LLM Client for Multi-Agent E-commerce Trust Intelligence System.
Supports Google Gemini (gemini-3.8-flash primary) with resilient fallback and Groq.
Maintains a complete, verbose audit log of all prompts, completions, and execution traces.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("TrustAgentLLM")
logger.setLevel(logging.INFO)


class AgentAuditLogger:
    """Collects and stores granular execution logs for all agents."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logs = []
        return cls._instance

    def log_event(self, agent_id: int, agent_name: str, event_type: str, data: Dict[str, Any]):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "event_type": event_type,
            "data": data
        }
        self.logs.append(entry)
        logger.info(f"[{agent_name}] {event_type}: {str(data)[:120]}")

    def get_logs(self) -> List[Dict[str, Any]]:
        return list(self.logs)

    def clear(self):
        self.logs.clear()


audit_logger = AgentAuditLogger()


class TrustAgentLLMClient:
    """
    Centralized LLM client supporting Google Gemini (gemini-3.8-flash)
    and Groq (openai/gpt-oss-120b).
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.preferred_gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.fallback_gemini_model = "gemini-3.5-flash-lite"
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def is_available(self) -> bool:
        return bool(self.gemini_key or self.groq_key)

    def call_gemini(self, prompt: str, system_instruction: str = "", timeout: int = 15) -> Tuple[Optional[str], str, float]:
        """
        Calls Gemini REST API. Tries gemini-3.8-flash first as instructed.
        Falls back to gemini-3.5-flash-lite if 3.8 encounters 503 high demand spike.
        Returns: (response_text, model_used, latency_ms)
        """
        if not self.gemini_key:
            return None, "none", 0.0

        models_to_try = [self.preferred_gemini_model, self.fallback_gemini_model]
        
        for model in models_to_try:
            t0 = time.perf_counter()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048,
                }
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "").strip()
                            return text, model, elapsed_ms
                elif resp.status_code == 503:
                    logger.warning(f"Gemini model {model} returned 503 high demand. Trying next model...")
                    continue
                else:
                    logger.warning(f"Gemini {model} returned status {resp.status_code}: {resp.text[:150]}")
            except Exception as e:
                logger.warning(f"Gemini {model} exception: {e}")
                continue

        return None, "failed", 0.0

    def call_groq(self, prompt: str, system_instruction: str = "", timeout: int = 15) -> Tuple[Optional[str], str, float]:
        """Calls Groq API as an alternative high-speed LLM engine."""
        if not self.groq_key:
            return None, "none", 0.0

        t0 = time.perf_counter()
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            completion = client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=0.1,
                timeout=timeout
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            text = (completion.choices[0].message.content or "").strip()
            return text, f"groq:{self.groq_model}", elapsed_ms
        except Exception as e:
            logger.warning(f"Groq API error: {e}")
            return None, "groq:failed", 0.0

    def generate(self, prompt: str, system_instruction: str = "", prefer: str = "gemini") -> Tuple[Optional[str], str, float]:
        """
        Unified generation method.
        Primary: Gemini (gemini-3.8-flash)
        Secondary: Groq (openai/gpt-oss-120b)
        """
        if prefer == "gemini" and self.gemini_key:
            res, model, latency = self.call_gemini(prompt, system_instruction)
            if res:
                return res, model, latency
            if self.groq_key:
                res_g, model_g, latency_g = self.call_groq(prompt, system_instruction)
                if res_g:
                    return res_g, model_g, latency_g
        elif self.groq_key:
            res, model, latency = self.call_groq(prompt, system_instruction)
            if res:
                return res, model, latency
            if self.gemini_key:
                res_gem, model_gem, latency_gem = self.call_gemini(prompt, system_instruction)
                if res_gem:
                    return res_gem, model_gem, latency_gem

        return None, "none", 0.0
