"""
agents/storage.py
Persistent Data Storage Layer for Autonomous Trust Intelligence System.
Uses SQLite with WAL mode to record and manage:
- Longitudinal Product Listing Audits & Evidentiary Dossiers
- Interactive Reviewer Chat History & Session Logs
- Safety Guardrail Violation & Sanitization Telemetry
- RAG Statutory Knowledge Base Chunks
"""

import os
import json
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trust_agent.db")


class TrustStorage:
    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Product Audits Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT NOT NULL,
                product_title TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                price REAL,
                seller_name TEXT,
                seller_id TEXT,
                engine_mode TEXT,
                overall_trust_score REAL,
                risk_tier TEXT,
                compliance_score REAL,
                authenticity_score REAL,
                seller_score REAL,
                image_score REAL,
                velocity_spike_detected BOOLEAN,
                reviews_count INTEGER,
                cohorts_count INTEGER,
                recommended_verdict TEXT,
                evidence_json TEXT,
                redlines_json TEXT,
                timeline_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Chat History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                guardrail_status TEXT DEFAULT 'PASSED',
                sources_cited_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 3. Guardrail Telemetry Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS guardrail_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                raw_input TEXT,
                sanitized_output TEXT,
                action_taken TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 4. RAG Statutory Knowledge Base Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                authority TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            conn.commit()

        # Seed knowledge base if empty
        self._seed_default_rag_knowledge()

    def _seed_default_rag_knowledge(self):
        """Seeds canonical statutory rules, marketplace policies, and benchmarks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM rag_knowledge;")
            count = cursor.fetchone()["cnt"]
            if count > 0:
                return

            seed_data = [
                (
                    "DOC_FDA_DSHEA",
                    "Statutory Regulation",
                    "FDA DSHEA § 403(r) - Dietary Supplement Disease Claims",
                    "Under the Dietary Supplement Health and Education Act of 1994 (DSHEA) and 21 U.S.C. 343(r)(6), dietary supplements and herbal gummies cannot claim to diagnose, treat, cure, mitigate, or prevent any specific disease (such as diabetes, hypertension, or obesity). Such assertions classify the product as an unapproved new drug under Section 505 of the FD&C Act, warranting immediate delisting and FDA Warning Letters.",
                    "U.S. Food & Drug Administration (FDA)",
                    "supplements, health, medical claim, diabetes, cure, fda"
                ),
                (
                    "DOC_BIS_IS13252",
                    "Statutory Regulation",
                    "BIS IS 13252 / IS 16046 - Compulsory Registration Scheme for Electronics",
                    "The Bureau of Indian Standards (BIS) mandates Compulsory Registration Scheme (CRS) for all lithium-ion power banks, cells, and adapters under IS 13252 (Part 1):2010 and IS 16046. Any listing sold on e-commerce platforms in India without a verifiable 8-digit R-number (e.g., R-41012345) is non-compliant and subject to seizure under the Consumer Protection (E-Commerce) Rules 2020.",
                    "Bureau of Indian Standards (Govt. of India)",
                    "electronics, power bank, battery, bis, registration, crs"
                ),
                (
                    "DOC_UL_2056",
                    "Safety Standards",
                    "UL 2056 Standard for Safety of Power Banks",
                    "UL 2056 outlines specific electrical and thermal safety evaluation criteria for portable power banks. Marketers claiming 'UL Certified' must possess an active UL Listing File Number. Unsubstantiated 'military-grade' or 'UL tested' marks without official certificate verification constitute deceptive advertising under FTC Section 5.",
                    "Underwriters Laboratories (UL Standards)",
                    "ul, safety, power bank, battery, military-grade, overcharge"
                ),
                (
                    "DOC_FTC_REVIEWS",
                    "Marketplace Guideline",
                    "FTC 16 CFR Part 255 - Synthetic & Incentivized Review Enforcement",
                    "The Federal Trade Commission guidelines on endorsements and testimonials strictly prohibit fake reviews created by non-genuine buyers, bot syndicates, or through undisclosed incentives. Velocity bursts characterized by >3x baseline volume in 48 hours with >80% unverified purchase ratios constitute strong empirical evidence of coordinated review manipulation.",
                    "Federal Trade Commission (FTC)",
                    "reviews, fake reviews, velocity burst, unverified purchase, bots"
                ),
                (
                    "DOC_COSMETICS_ACT",
                    "Statutory Regulation",
                    "Drugs and Cosmetics Act 1940 & Rules (India) - IS 4707 Standards",
                    "Cosmetics, including lip care, skin tints, and topical creams, must adhere strictly to IS 4707 safety standards regarding permitted colorants and preservative concentrations. Counterfeit cosmetic imitations using fraudulent batch codes or unauthorized manufacturing origin (e.g. imitation formulas causing lip swelling/chemical irritation) violate Sections 18(a) and 27A, subjecting the merchant to immediate platform ban and statutory prosecution.",
                    "Ministry of Health & Family Welfare (CDSCO)",
                    "cosmetics, lip tint, rhode, counterfeit, toxic, chemical burn, fake"
                ),
                (
                    "DOC_LISTING_DRIFT",
                    "Marketplace Guideline",
                    "Marketplace Anti-Hijacking & Catalog Integrity Guidelines",
                    "Listing drift occurs when a merchant takes over an established, highly-reviewed ASIN/SKU and swaps the underlying product, title, or manufacturer origin to exploit existing ratings. Key indicators include: sudden price reductions (>60%), merchant account age <30 days with thousands of legacy reviews, and customer reports of typographic errors on physical packaging.",
                    "Amazon / Flipkart Trust & Safety Global Standards",
                    "listing drift, asin hijack, price dump, shell seller, origin swap"
                )
            ]

            cursor.executemany("""
            INSERT INTO rag_knowledge (chunk_id, category, title, content, authority, tags)
            VALUES (?, ?, ?, ?, ?, ?);
            """, seed_data)
            conn.commit()

    # --- Audit Operations ---
    def save_audit_report(self, report_data: Dict[str, Any]) -> int:
        """Saves a completed trust audit report into persistent storage."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_records (
                listing_id, product_title, brand, category, price,
                seller_name, seller_id, engine_mode, overall_trust_score,
                risk_tier, compliance_score, authenticity_score, seller_score, image_score,
                velocity_spike_detected, reviews_count, cohorts_count, recommended_verdict,
                evidence_json, redlines_json, timeline_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                report_data.get("listing_id", "N/A"),
                report_data.get("product_name", "N/A"),
                report_data.get("brand", "N/A"),
                report_data.get("category", "N/A"),
                float(report_data.get("price", 0.0)),
                report_data.get("seller_name", "N/A"),
                report_data.get("seller_id", "N/A"),
                report_data.get("engine_mode", "Heuristic Demo"),
                float(report_data.get("overall_trust_score", 0.0)),
                report_data.get("risk_tier", "HIGH RISK"),
                float(report_data.get("compliance_score", 0.0)),
                float(report_data.get("authenticity_score", 0.0)),
                float(report_data.get("seller_score", 0.0)),
                float(report_data.get("image_score", 0.0)),
                bool(report_data.get("velocity_spike_detected", False)),
                int(report_data.get("reviews_count", 0)),
                int(report_data.get("cohorts_count", 0)),
                report_data.get("recommended_verdict", ""),
                json.dumps(report_data.get("itemized_evidence", [])),
                json.dumps(report_data.get("redline_suggestions", [])),
                json.dumps(report_data.get("agent_timeline", []))
            ))
            conn.commit()
            return cursor.lastrowid

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves past audit runs ordered by newest first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM audit_records
            ORDER BY created_at DESC
            LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_audit_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific audit record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_records WHERE id = ?;", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Chat Operations ---
    def save_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        guardrail_status: str = "PASSED",
        sources_cited: Optional[List[str]] = None
    ) -> int:
        """Saves a user or assistant chat message."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO chat_history (session_id, role, content, guardrail_status, sources_cited_json)
            VALUES (?, ?, ?, ?, ?);
            """, (
                session_id,
                role,
                content,
                guardrail_status,
                json.dumps(sources_cited or [])
            ))
            conn.commit()
            return cursor.lastrowid

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves conversation history for a specific session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM chat_history
            WHERE session_id = ?
            ORDER BY created_at ASC;
            """, (session_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("sources_cited_json"):
                    try:
                        item["sources_cited"] = json.loads(item["sources_cited_json"])
                    except Exception:
                        item["sources_cited"] = []
                else:
                    item["sources_cited"] = []
                result.append(item)
            return result

    def clear_chat_history(self, session_id: str):
        """Clears conversation messages for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?;", (session_id,))
            conn.commit()

    # --- Guardrail Events ---
    def log_guardrail_event(
        self,
        event_type: str,
        severity: str,
        raw_input: str,
        sanitized_output: str,
        action_taken: str,
        details: str
    ):
        """Logs a safety guardrail event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO guardrail_events (
                event_type, severity, raw_input, sanitized_output, action_taken, details
            ) VALUES (?, ?, ?, ?, ?, ?);
            """, (event_type, severity, raw_input, sanitized_output, action_taken, details))
            conn.commit()

    def get_guardrail_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent guardrail events."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guardrail_events ORDER BY created_at DESC LIMIT ?;", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # --- RAG Knowledge Queries ---
    def get_all_knowledge_chunks(self) -> List[Dict[str, Any]]:
        """Retrieves all statutory and catalog compliance chunks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rag_knowledge ORDER BY id ASC;")
            return [dict(r) for r in cursor.fetchall()]
