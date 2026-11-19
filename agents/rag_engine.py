"""
Retrieval-Augmented Generation (RAG) Engine for E-commerce Trust Intelligence.
Indexes statutory compliance rules (FDA DSHEA, BIS IS 13252, UL 2056, FTC 16 CFR 255, CDSCO)
from SQLite using BM25 retrieval and answers reviewer queries strictly via live LLM grounding.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

from agents.llm_client import TrustAgentLLMClient
from agents.storage import TrustStorage


class RAGDocumentChunk:
    def __init__(self, chunk_id: str, title: str, content: str, authority: str, tags: str) -> None:
        self.chunk_id = chunk_id
        self.title = title
        self.content = content
        self.authority = authority
        self.tags = tags
        self.tokens = self._tokenize(f"{title} {content} {tags}")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())


class TrustRAGEngine:
    def __init__(self, storage: Optional[TrustStorage] = None) -> None:
        self.storage = storage or TrustStorage()
        self.corpus: List[RAGDocumentChunk] = []
        self._load_and_index_corpus()

    def _load_and_index_corpus(self) -> None:
        self.corpus = []
        for row in self.storage.get_all_knowledge_chunks():
            self.corpus.append(
                RAGDocumentChunk(
                    chunk_id=row["chunk_id"],
                    title=row["title"],
                    content=row["content"],
                    authority=row["authority"],
                    tags=row.get("tags", ""),
                )
            )

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k statutory guidelines using Okapi BM25 scoring."""
        q_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query.lower())
        if not q_tokens or not self.corpus:
            return []

        doc_count = len(self.corpus)
        avg_dl = sum(len(c.tokens) for c in self.corpus) / max(1, doc_count)
        scores: List[tuple[float, RAGDocumentChunk]] = []

        for chunk in self.corpus:
            score = 0.0
            doc_len = len(chunk.tokens)
            for qt in q_tokens:
                tf = chunk.tokens.count(qt)
                if tf > 0:
                    df = sum(1 for c in self.corpus if qt in c.tokens)
                    idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)
                    k1, b = 1.2, 0.75
                    tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / max(1.0, avg_dl))))
                    boost = 2.0 if qt in chunk.title.lower() else (1.5 if qt in chunk.tags.lower() else 1.0)
                    score += tf_norm * idf * boost
            if score > 0.05:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "content": chunk.content,
                "authority": chunk.authority,
                "relevance_score": round(score, 3),
            }
            for score, chunk in scores[:top_k]
        ]

    def answer_reviewer_query(
        self,
        query: str,
        llm_client: TrustAgentLLMClient,
        current_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Answers a Trust & Safety reviewer query via live LLM grounded in retrieved statutory chunks + current dossier."""
        retrieved_docs = self.retrieve(query, top_k=3)
        sources_cited = [f"{d['title']} ({d['authority']})" for d in retrieved_docs]

        listing_facts = ""
        if current_report:
            ev_lines = "\n".join(
                f"  - [{e.get('risk_level')}] {e.get('module')}: {e.get('issue')}"
                for e in (current_report.get("itemized_evidence") or [])[:6]
            )
            listing_facts = (
                f"\nCURRENT LISTING DOSSIER:\n"
                f"- Product: {current_report.get('product_name')}\n"
                f"- Seller: {current_report.get('seller_name')} ({current_report.get('seller_id')})\n"
                f"- Overall Trust Score: {current_report.get('overall_trust_score')}/100 ({current_report.get('risk_tier')})\n"
                f"- Component Scores: Compliance={current_report.get('compliance_score')}, "
                f"Authenticity={current_report.get('authenticity_score')}, "
                f"Seller={current_report.get('seller_score')}, Image={current_report.get('image_integrity_score')}\n"
                f"- Velocity Spike Detected: {current_report.get('velocity_spike_detected')}\n"
                f"- Key Evidence:\n{ev_lines or '  - None flagged'}\n"
            )

        context_block = (
            "\n\n".join(
                f"[{d['chunk_id']}] {d['title']} ({d['authority']}):\n{d['content']}"
                for d in retrieved_docs
            )
            or "No specific statutory regulation chunk matched; rely strictly on the current listing dossier."
        )

        system_instruction = (
            "You are the Trust & Safety Statutory RAG Assistant. Answer concisely and accurately using ONLY "
            "the provided regulatory guidelines and current listing audit dossier. Cite specific regulations when relevant."
        )
        prompt = (
            f"RETRIEVED STATUTORY KNOWLEDGE BASE:\n{context_block}\n"
            f"{listing_facts}\n"
            f"REVIEWER QUESTION: {query}"
        )

        ans_text, model_used, latency_ms = llm_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=False,
        )
        return {
            "answer": ans_text,
            "model_used": model_used,
            "latency_ms": latency_ms,
            "sources_cited": sources_cited,
            "retrieved_chunks": retrieved_docs,
        }
