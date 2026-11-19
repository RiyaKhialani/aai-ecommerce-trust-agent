"""
Agent 1: Listing Ingestion Agent
Scrapes live marketplace URLs via Jina Reader (with direct HTTP + BeautifulSoup fallback)
and parses structured listing fields using the live LLM. Also supports direct JSON/text
listing payloads when a user supplies structured listing data.
Zero offline catalogs and zero fake fallback records.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from agents.llm_client import TrustAgentLLMClient
from agents.schemas import ProductListing, ReviewItem


class LiveScrapeError(RuntimeError):
    """Raised when a live marketplace URL cannot be fetched or parsed."""


class ListingIngestionAgent:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    BLOCKED_PHRASES = [
        "503 - service unavailable error",
        "503 service unavailable",
        "service unavailable error",
        "503 - service unavailable",
        "502 bad gateway",
        "504 gateway time-out",
        "enter the characters you see below",
        "click the button below to continue shopping",
        "sorry, we just need to make sure you're not a robot",
        "to discuss automated access to amazon data please contact",
        "api rate limit exceeded",
    ]

    def __init__(self) -> None:
        self.agent_id = 1
        self.name = "Listing Ingestion Agent"

    @classmethod
    def _is_blocked_or_error(cls, text: str) -> bool:
        if not text:
            return True
        low = text.lower()
        return any(phrase in low for phrase in cls.BLOCKED_PHRASES)

    @staticmethod
    def clean_url(url: str) -> str:
        raw = url.strip()
        if not raw:
            raise LiveScrapeError("Please enter a valid product URL.")
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
        parsed = urlparse(raw)
        netloc = parsed.netloc.lower()
        if "amazon." in netloc:
            m = re.search(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})", raw, re.IGNORECASE)
            if m:
                return f"https://{netloc}/dp/{m.group(1).upper()}"
        return urlunparse(parsed._replace(fragment=""))

    def fetch_live_page(self, url: str, timeout: int = 18) -> Dict[str, Any]:
        canonical = self.clean_url(url)
        raw_text = ""
        image_urls: List[str] = []
        method = ""

        # Extract ASIN if Amazon URL
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", canonical, re.IGNORECASE)
        asin = asin_match.group(1).upper() if asin_match else ""

        # 1. Primary: Jina Reader live markdown stream
        for candidate in dict.fromkeys([canonical, url.strip()]):
            try:
                resp = requests.get(
                    f"https://r.jina.ai/{candidate}",
                    headers={"User-Agent": self.USER_AGENT, "X-No-Cache": "true"},
                    timeout=timeout,
                )
                if resp.status_code == 200 and len(resp.text.strip()) > 300:
                    body = resp.text.strip()
                    if not self._is_blocked_or_error(body):
                        raw_text = body
                        method = "Jina Reader Live Stream"
                        image_urls = list(
                            dict.fromkeys(
                                re.findall(r"https://[^\s\)\"']+\.(?:jpg|jpeg|png|webp)", body, re.IGNORECASE)
                            )
                        )[:6]
                        break
            except requests.RequestException:
                continue

        # 2. Fallback: Direct HTTP with desktop browser headers + BeautifulSoup4
        if not raw_text:
            browser_headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
            try:
                resp = requests.get(
                    canonical,
                    headers=browser_headers,
                    timeout=timeout,
                )
                if resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    page_title = str(soup.title.string).strip() if soup.title else ""
                    if not self._is_blocked_or_error(page_title):
                        og_img = soup.find("meta", property="og:image")
                        if og_img and og_img.get("content"):
                            image_urls.append(str(og_img["content"]).strip())
                        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
                            tag.decompose()
                        body = soup.get_text(separator="\n", strip=True)
                        if len(body) > 250 and not self._is_blocked_or_error(body):
                            raw_text = body
                            method = "Direct HTTP + BeautifulSoup4"
            except requests.RequestException:
                pass

        # 3. Fallback: DuckDuckGo Search Meta Lookup (recovers real product specs when Amazon returns 503)
        if not raw_text and asin:
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    query = f"site:amazon.in dp/{asin}"
                    hits = list(ddgs.text(query, max_results=3))
                    if not hits:
                        hits = list(ddgs.text(f"{asin} amazon product", max_results=3))
                    if hits:
                        best = hits[0]
                        title = best.get("title", "").replace("Amazon.in:", "").replace("Buy ", "").strip()
                        body_desc = "\n".join(h.get("body", "") for h in hits)
                        if title and not self._is_blocked_or_error(title):
                            raw_text = (
                                f"Product Title: {title}\n"
                                f"ASIN: {asin}\n"
                                f"Product Specifications & Overview: {body_desc}\n"
                                f"Source URL: {canonical}"
                            )
                            method = "DuckDuckGo Search Metadata Recovery"
            except Exception:
                pass

        if not raw_text:
            raise LiveScrapeError(
                f"Amazon or the marketplace returned a 503 Service Unavailable / bot challenge for '{canonical}'. "
                "Automated scrapers are temporarily blocked from fetching this direct page. "
                "Please switch to 'Paste Listing Text' in the sidebar and paste the product title & description directly."
            )

        return {
            "canonical_url": canonical,
            "raw_text": raw_text[:22000],
            "image_urls": image_urls,
            "method": method,
        }

    def execute_from_url(self, url: str, llm_client: TrustAgentLLMClient) -> ProductListing:
        fetched = self.fetch_live_page(url)
        return self._parse_with_llm(
            raw_text=fetched["raw_text"],
            source_url=fetched["canonical_url"],
            image_urls=fetched["image_urls"],
            llm_client=llm_client,
        )

    def execute_from_text(
        self,
        raw_text: str,
        llm_client: TrustAgentLLMClient,
        source_url: Optional[str] = None,
    ) -> ProductListing:
        if not raw_text or len(raw_text.strip()) < 30:
            raise LiveScrapeError("Please provide at least 30 characters of real product listing text to audit.")
        return self._parse_with_llm(
            raw_text=raw_text.strip()[:22000],
            source_url=source_url,
            image_urls=[],
            llm_client=llm_client,
        )

    def _parse_with_llm(
        self,
        raw_text: str,
        source_url: Optional[str],
        image_urls: List[str],
        llm_client: TrustAgentLLMClient,
    ) -> ProductListing:
        """Uses the live LLM to extract structured listing fields and real customer reviews."""
        system_prompt = (
            "You are Agent 1 (Listing Ingestion Agent) in an E-Commerce Trust & Safety pipeline. "
            "Extract ONLY real facts explicitly present in the provided product listing text. "
            "Never fabricate reviews, prices, or seller account ages that are not stated."
        )
        user_prompt = f"""
Source URL: {source_url or 'Direct Listing Paste'}

Raw Product Page Text:
{raw_text[:16000]}

Return strict JSON matching this schema:
{{
  "listing_id": "ASIN or SKU from page, or empty string if absent",
  "title": "Exact product title",
  "description": "Concise factual summary of product description and claims from the page (up to 1200 chars)",
  "brand": "Brand name or 'Unknown'",
  "category": "Product category (e.g. Electronics, Beauty & Personal Care, Health & Supplements, Audio)",
  "price": 0.0,
  "original_mrp": null,
  "currency": "INR or USD",
  "seller_name": "Seller/merchant name if stated, else 'Unknown Seller'",
  "origin_country": "Country of origin if stated, else null",
  "seller_account_age_days": null,
  "seller_rating": 0.0,
  "specs": {{
    "Spec Name": "Exact Value"
  }},
  "reviews": [
    {{
      "review_id": "rev-1",
      "reviewer_id": "Reviewer name or ID from page",
      "rating": 5.0,
      "title": "Review title",
      "text": "Exact review excerpt from page",
      "timestamp": "YYYY-MM-DD if stated, else 'Unknown'",
      "verified_purchase": true,
      "helpful_votes": 0
    }}
  ]
}}
"""
        parsed, _, _ = llm_client.generate_json(user_prompt, system_instruction=system_prompt)

        fallback_id = "LIVE-" + hashlib.md5((source_url or raw_text[:200]).encode("utf-8")).hexdigest()[:8].upper()
        listing_id = str(parsed.get("listing_id") or "").strip() or fallback_id
        price = float(parsed.get("price") or 0.0)
        mrp_raw = parsed.get("original_mrp")
        original_mrp = float(mrp_raw) if mrp_raw not in (None, "", 0, "null") else None

        price_history: List[Dict[str, Any]] = []
        if original_mrp and original_mrp > 0:
            price_history.append({"date": "M.R.P. Baseline", "price": original_mrp})
        if price > 0:
            price_history.append({"date": "Current Listed Price", "price": price})

        reviews: List[ReviewItem] = []
        for idx, r in enumerate(parsed.get("reviews") or [], start=1):
            if not isinstance(r, dict):
                continue
            r_text = str(r.get("text") or "").strip()
            if not r_text:
                continue
            reviews.append(
                ReviewItem(
                    review_id=str(r.get("review_id") or f"rev-{idx}"),
                    reviewer_id=str(r.get("reviewer_id") or f"buyer-{idx}"),
                    rating=float(r.get("rating") or 0.0),
                    title=str(r.get("title") or "Customer Review"),
                    text=r_text[:500],
                    timestamp=str(r.get("timestamp") or "Unknown"),
                    verified_purchase=bool(r.get("verified_purchase", True)),
                    helpful_votes=int(r.get("helpful_votes") or 0),
                )
            )

        specs_clean = {
            str(k): str(v)
            for k, v in (parsed.get("specs") or {}).items()
            if v is not None and str(v).strip()
        }
        if parsed.get("origin_country"):
            specs_clean.setdefault("Country of Origin", str(parsed["origin_country"]))

        seller_name = str(parsed.get("seller_name") or "Unknown Seller").strip()
        seller_id = "SELL-" + hashlib.md5(seller_name.encode("utf-8")).hexdigest()[:6].upper()
        age_raw = parsed.get("seller_account_age_days")
        seller_age = int(age_raw) if age_raw not in (None, "", "null") else None

        product_title = str(parsed.get("title") or "Untitled Listing").strip()
        if self._is_blocked_or_error(product_title):
            raise LiveScrapeError(
                f"Marketplace returned a 503 Service Unavailable / bot challenge for '{source_url or 'URL'}'. "
                "The actual product details could not be loaded. Please paste the product title and description into the 'Paste Listing Text' tab."
            )

        return ProductListing(
            listing_id=listing_id,
            title=product_title,
            description=str(parsed.get("description") or raw_text[:1500]).strip(),
            brand=str(parsed.get("brand") or "Unknown").strip(),
            category=str(parsed.get("category") or "General Merchandise").strip(),
            price=price,
            original_mrp=original_mrp,
            currency=str(parsed.get("currency") or "INR").strip(),
            seller_id=seller_id,
            seller_name=seller_name,
            origin_country=parsed.get("origin_country"),
            seller_account_age_days=seller_age,
            seller_rating=float(parsed.get("seller_rating") or 0.0),
            price_history=price_history,
            image_urls=image_urls,
            specs=specs_clean,
            url=source_url,
            reviews=reviews,
        )
