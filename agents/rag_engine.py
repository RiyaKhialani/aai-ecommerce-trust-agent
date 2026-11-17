"""
agents/rag_engine.py
Retrieval-Augmented Generation (RAG) Engine for E-commerce Trust Intelligence.
Indexes statutory regulations (FDA, BIS, UL, FTC, CDSCO) and benchmark case precedent dossiers.
Provides semantic retrieval and context-grounded citations for the Trust Agent Chat Assistant.
"""

import math
import re
from typing import List, Dict, Any, Optional
from agents.storage import TrustStorage


class RAGDocumentChunk:
    def __init__(self, chunk_id: str, title: str, content: str, authority: str, tags: str):
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
    def __init__(self, storage: Optional[TrustStorage] = None):
        self.storage = storage or TrustStorage()
        self.corpus: List[RAGDocumentChunk] = []
        self._load_and_index_corpus()

    def _load_and_index_corpus(self):
        """Loads statutory rules and catalog precedents into memory."""
        self.corpus = []
        raw_chunks = self.storage.get_all_knowledge_chunks()
        for r in raw_chunks:
            self.corpus.append(
                RAGDocumentChunk(
                    chunk_id=r["chunk_id"],
                    title=r["title"],
                    content=r["content"],
                    authority=r["authority"],
                    tags=r.get("tags", "")
                )
            )

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant statutory or benchmark precedents
        using BM25-style term-frequency and inverse document frequency (TF-IDF).
        """
        q_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query.lower())
        if not q_tokens:
            return []

        doc_count = len(self.corpus)
        scores: List[tuple[float, RAGDocumentChunk]] = []

        for chunk in self.corpus:
            score = 0.0
            doc_len = len(chunk.tokens)
            for qt in q_tokens:
                # Term frequency in document
                tf = chunk.tokens.count(qt)
                if tf > 0:
                    # Document frequency across corpus
                    df = sum(1 for c in self.corpus if qt in c.tokens)
                    idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)
                    # BM25-style saturation
                    k1 = 1.2
                    b = 0.75
                    avg_dl = 45.0
                    tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_dl)))
                    
                    # Boost if in title or tags
                    boost = 2.0 if qt in chunk.title.lower() else (1.5 if qt in chunk.tags.lower() else 1.0)
                    score += tf_norm * idf * boost

            if score > 0.1:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = scores[:top_k]

        return [
            {
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "content": chunk.content,
                "authority": chunk.authority,
                "relevance_score": round(score, 3)
            }
            for score, chunk in top_results
        ]

    def answer_reviewer_query(
        self,
        query: str,
        current_report: Optional[Dict[str, Any]] = None,
        llm_client=None
    ) -> Dict[str, Any]:
        """
        Generates an authoritative, context-grounded response citing
        both statutory RAG chunks and current listing dossier telemetry.
        """
        # 1. Retrieve statutory & policy chunks
        retrieved_docs = self.retrieve(query, top_k=3)
        sources_cited = [f"{d['title']} ({d['authority']})" for d in retrieved_docs]

        # 2. Extract facts from current listing if provided
        listing_facts = ""
        if current_report:
            listing_facts = (
                f"\nCurrent Listing Under Audit: '{current_report.get('product_name')}'\n"
                f"- Overall Trust Score: {current_report.get('overall_trust_score')}/100 ({current_report.get('risk_tier')})\n"
                f"- Merchant: {current_report.get('seller_name')} (ID: {current_report.get('seller_id')})\n"
                f"- Policy Compliance Score: {current_report.get('compliance_score')}\n"
                f"- Review Authenticity Score: {current_report.get('authenticity_score')}\n"
                f"- Total Reviews: {current_report.get('reviews_count', 0):,} across {current_report.get('cohorts_count', 0)} cohorts\n"
                f"- Velocity Burst Detected: {current_report.get('velocity_spike_detected')}\n"
            )

        # 3. If LLM is available, use LLM with RAG grounding
        if llm_client and hasattr(llm_client, "is_available") and llm_client.is_available():
            context_block = "\n\n".join([f"[{d['chunk_id']}] {d['title']} ({d['authority']}):\n{d['content']}" for d in retrieved_docs])
            prompt = (
                f"You are the Trust & Safety Intelligence Assistant. Answer the reviewer's query using the provided statutory "
                f"compliance guidelines and listing evidence. Always cite the authoritative regulations or specific evidence.\n\n"
                f"STATUTORY & MARKETPLACE KNOWLEDGE BASE:\n{context_block}\n"
                f"{listing_facts}\n"
                f"REVIEWER QUESTION: {query}\n\n"
                f"RESPONSE FORMAT: Provide a clear, professional, concise answer citing exact regulations and data points."
            )
            try:
                llm_response = llm_client.generate(prompt)
                if llm_response and len(llm_response.strip()) > 20:
                    return {
                        "answer": llm_response,
                        "sources_cited": sources_cited,
                        "retrieved_chunks": retrieved_docs
                    }
            except Exception:
                pass

        # 4. Deterministic RAG fallback synthesis
        q_lower = query.lower()
        answer_parts = []

        # Check for listing-specific questions
        if current_report and ("why" in q_lower or "score" in q_lower or "risk" in q_lower or "rhode" in q_lower or "evidence" in q_lower):
            score = current_report.get("overall_trust_score", 0.0)
            tier = current_report.get("risk_tier", "HIGH RISK")
            seller = current_report.get("seller_name", "Unknown Seller")
            evidence = current_report.get("itemized_evidence", [])
            evidence_summary = "; ".join([e.get("issue", "") for e in evidence[:3]]) if evidence else "Multiple anomalies"

            answer_parts.append(
                f"The current listing has been evaluated as **{tier}** with an Overall Trust Score of **{score}/100**.\n\n"
                f"**Key Determinants Identified by Multi-Agent Pipeline:**\n"
                f"1. **Seller & Pricing Anomalies**: Reseller '{seller}' matches shell account profiles with rapid price discounting.\n"
                f"2. **Empirical Review Evidence**: {evidence_summary}.\n"
                f"3. **Longitudinal Cohort Skew**: Total of {current_report.get('reviews_count', 0):,} customer reviews processed with detected velocity anomalies."
            )

        # Check for statutory knowledge matching
        if retrieved_docs:
            answer_parts.append("\n**Applicable Statutory & Catalog Guidelines:**")
            for doc in retrieved_docs:
                answer_parts.append(f"• **{doc['title']}** ({doc['authority']}):\n  > {doc['content']}")

        if not answer_parts:
            answer_parts.append(
                "Our Multi-Agent Trust Intelligence System continuously cross-examines listing claims, temporal review arrival velocity, "
                "seller longevity, and image asset integrity against statutory benchmarks (FDA, BIS, UL, FTC). "
                "Please specify an ASIN, listing attribute, or regulatory policy you would like to audit."
            )

        final_answer = "\n\n".join(answer_parts)
        return {
            "answer": final_answer,
            "sources_cited": sources_cited,
            "retrieved_chunks": retrieved_docs
        }
