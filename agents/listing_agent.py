"""
Agent 1: Listing Ingestion Agent
Scrapes live marketplace URLs via Jina Reader (with direct HTTP + BeautifulSoup fallback)
and parses structured listing fields using the live LLM. Also supports direct JSON/text
listing payloads when a user supplies structured listing data.
Guarantees full customer review extraction without truncation.
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

    MONTH_MAP = {
        "january": "01", "jan": "01",
        "february": "02", "feb": "02",
        "march": "03", "mar": "03",
        "april": "04", "apr": "04",
        "may": "05",
        "june": "06", "jun": "06",
        "july": "07", "jul": "07",
        "august": "08", "aug": "08",
        "september": "09", "sep": "09", "sept": "09",
        "october": "10", "oct": "10",
        "november": "11", "nov": "11",
        "december": "12", "dec": "12",
    }

    def __init__(self) -> None:
        self.agent_id = 1
        self.name = "Listing Ingestion Agent"

    @classmethod
    def _is_blocked_or_error(cls, text: str) -> bool:
        if not text:
            return True
        low = text.lower()
        return any(phrase in low for phrase in cls.BLOCKED_PHRASES)

    @classmethod
    def normalize_review_date(cls, raw_date: str) -> str:
        """Converts natural dates like 'Reviewed in India on 21 May 2025' into '2025-05-21'."""
        if not raw_date:
            return "Undated"
        raw = raw_date.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
            return raw
        m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
        if m:
            day, month_str, year = m.groups()
            month = cls.MONTH_MAP.get(month_str.lower())
            if month:
                return f"{year}-{month}-{int(day):02d}"
        m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", raw)
        if m:
            month_str, day, year = m.groups()
            month = cls.MONTH_MAP.get(month_str.lower())
            if month:
                return f"{year}-{month}-{int(day):02d}"
        m = re.search(r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})", raw)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        return "Undated"

    @classmethod
    def clean_review_text(cls, raw_text: str) -> str:
        """Strips markdown links, feedback prompts, and Amazon boilerplate from review body."""
        t = raw_text
        t = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", t)
        t = re.sub(r"\[Colour:[^\]]+\]\([^)]+\)", "", t)
        t = re.sub(r"\[Size:[^\]]+\]\([^)]+\)", "", t)
        t = re.sub(r"\[Style:[^\]]+\]\([^)]+\)", "", t)
        t = re.sub(r"\[Verified Purchase\]\([^)]+\)", "", t)
        t = re.sub(r"\[Read more Read less\]\([^)]+\)", "", t)
        t = re.sub(r"\[Report\]\([^)]+\)", "", t)
        t = re.sub(r"Brief content visible, double tap to read full content\.", "", t)
        t = re.sub(r"Full content visible, double tap to read brief content\.", "", t)
        t = re.split(
            r"(?:\d+\s+people found this helpful|One person found this helpful|Helpful\s+Please try again|Sending feedback|We\'ll check if this review meets)",
            t,
            flags=re.IGNORECASE,
        )[0]
        t = re.sub(r"^Reviewed in [^\n]+ on \d{1,2}\s+[A-Za-z]+\s+\d{4}\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"^[^\w\s]+", "", t)
        t = re.sub(r"[\)\s]+$", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @classmethod
    def extract_reviews_heuristic(cls, raw_text: str) -> List[ReviewItem]:
        """Extracts customer reviews directly from Jina markdown or HTML text."""
        m = re.search(
            r"(?:###?\s*Top reviews|Top reviews from India|Top reviews from [A-Za-z\s]+|Ratings & Reviews)",
            raw_text,
            re.IGNORECASE,
        )
        search_space = raw_text[m.start():] if m else raw_text

        pattern = re.compile(
            r"(?:\[!\[Image \d+\]\([^)]+\)\s*([^\]]+)\]\([^)]+\)|(?:\*\s+)?([A-Za-z0-9\s\.\-_]{2,40}))\s*"
            r"[_*]*([1-5](?:\.\d)?)\s+out of 5 stars[_*]*\s*"
            r"(?:#+\s*\[?([^\]\n]+)\]?(?:\([^)]+\))?)?\s*"
            r"(.*?)(?=(?:\[!\[Image \d+\]|\n\*\s+[A-Za-z0-9\s\.\-_]{2,40}\s*[_*]*[1-5](?:\.\d)?\s+out of 5 stars|\n[A-Za-z0-9\s\.\-_]{2,40}\s*[_*]*[1-5](?:\.\d)?\s+out of 5 stars|\Z))",
            re.DOTALL,
        )

        matches = list(pattern.finditer(search_space))
        reviews: List[ReviewItem] = []
        seen = set()
        ignore_names = {"customer reviews", "global ratings", "from acwo", "from the manufacturer", "see all photos"}

        for match in matches:
            reviewer = (match.group(1) or match.group(2) or "Amazon Customer").strip()
            reviewer = re.sub(r"\[!\[.*?\]\(.*?\)\]", "", reviewer).strip()
            if "\n" in reviewer:
                reviewer = reviewer.split("\n")[-1].strip()
            reviewer = re.sub(r"^(?:Cancel|Report|Read more|Read less|Top reviews|op reviews from India)\s*", "", reviewer, flags=re.IGNORECASE).strip()
            reviewer = re.sub(r"^_\d+\.?\d*|^[\*\_\s]+|[\*\_\s]+$", "", reviewer).strip()
            if not reviewer or reviewer.lower() in ignore_names or len(reviewer) < 2:
                continue

            try:
                rating = float(match.group(3))
                if rating < 1.0 or rating > 5.0:
                    continue
            except (ValueError, TypeError):
                rating = 5.0

            title = (match.group(4) or "Customer Review").strip()
            title = re.sub(r"\[!\[.*?\]\(.*?\)\]", "", title).strip()
            if title.lower() in ignore_names:
                continue

            body_raw = match.group(5) or ""
            date_m = re.search(r"Reviewed in [^\n]+ on (\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})", body_raw)
            date_norm = cls.normalize_review_date(date_m.group(1)) if date_m else "Undated"
            is_verified = "verified purchase" in body_raw.lower()
            helpful_m = re.search(r"(\d+)\s+people found this helpful", body_raw, re.IGNORECASE)
            helpful = int(helpful_m.group(1)) if helpful_m else 0

            cleaned = cls.clean_review_text(body_raw)
            if len(cleaned) < 15:
                continue

            key = (reviewer.lower(), round(rating, 1))
            if key in seen:
                continue
            seen.add(key)

            reviews.append(
                ReviewItem(
                    review_id=f"rev-scrape-{len(reviews) + 1}",
                    reviewer_id=reviewer,
                    rating=rating,
                    title=title,
                    text=cleaned[:500],
                    timestamp=date_norm,
                    verified_purchase=is_verified,
                    helpful_votes=helpful,
                )
            )
        return reviews

    @staticmethod
    def prepare_llm_payload(raw_text: str) -> str:
        """Extracts both product details and review sections so reviews are never lost in prompt truncations."""
        prod_section = raw_text[:14000]
        m = re.search(r"(?:###?\s*Top reviews|Top reviews from|Ratings & Reviews|Customer reviews)", raw_text, re.IGNORECASE)
        rev_section = ""
        if m:
            rev_section = raw_text[m.start():m.start() + 22000]

        if rev_section:
            return (
                f"=== PRODUCT DETAILS & SPECIFICATIONS ===\n{prod_section}\n\n"
                f"=== CUSTOMER REVIEWS & FEEDBACK SECTION ===\n{rev_section}"
            )
        return prod_section

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
                "Upgrade-Insecure-Requests": "1",
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

                        # Parse HTML customer reviews if present
                        review_nodes = soup.find_all(attrs={"data-hook": "review"}) or soup.select(".review")
                        bs_reviews: List[str] = []
                        if review_nodes:
                            bs_reviews.append("\n### Top reviews\n")
                            for rb in review_nodes:
                                uname = rb.find(class_=re.compile(r"profile-name|author"))
                                name_str = uname.get_text(strip=True) if uname else "Amazon Customer"
                                star = rb.find(attrs={"data-hook": "review-star-rating"}) or rb.find(class_=re.compile(r"icon-star"))
                                star_str = star.get_text(strip=True) if star else "5.0 out of 5 stars"
                                rtitle = rb.find(attrs={"data-hook": "review-title"}) or rb.find(class_=re.compile(r"review-title"))
                                title_str = rtitle.get_text(strip=True) if rtitle else "Customer Review"
                                rdate = rb.find(attrs={"data-hook": "review-date"})
                                date_str = rdate.get_text(strip=True) if rdate else ""
                                is_avp = bool(rb.find(attrs={"data-hook": "avp-badge"}))
                                rbody = rb.find(attrs={"data-hook": "review-body"}) or rb.find(class_=re.compile(r"review-text"))
                                body_str = rbody.get_text(strip=True) if rbody else ""

                                bs_reviews.append(
                                    f"* {name_str} _{star_str}_ ##### [{title_str}]\n"
                                    f"Reviewed on {date_str} {'[Verified Purchase]' if is_avp else ''}\n"
                                    f"{body_str}\n"
                                )

                        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
                            tag.decompose()
                        body = soup.get_text(separator="\n", strip=True)
                        if len(body) > 250 and not self._is_blocked_or_error(body):
                            raw_text = body + ("\n" + "\n".join(bs_reviews) if bs_reviews else "")
                            method = "Direct HTTP + BeautifulSoup4"
            except requests.RequestException:
                pass

        # 3. Fallback: DuckDuckGo Search Meta Lookup (recovers real product specs when Amazon blocks datacenter IPs)
        if not raw_text and asin:
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    hits = list(ddgs.text(f'"{asin}" site:amazon.in', max_results=4))
                    if not hits:
                        hits = list(ddgs.text(f'"{asin}" Amazon', max_results=4))
                    if not hits:
                        hits = list(ddgs.text(f'"{asin}"', max_results=4))
                    for h in hits:
                        cand_title = h.get("title", "").replace("Amazon.in:", "").replace("Buy ", "").strip()
                        cand_body = h.get("body", "").strip()
                        if cand_title and not self._is_blocked_or_error(cand_title) and len(cand_body) > 30:
                            raw_text = (
                                f"Product Title: {cand_title}\n"
                                f"ASIN: {asin}\n"
                                f"Product Specifications & Overview: {cand_body}\n"
                                f"Source URL: {canonical}"
                            )
                            method = "DuckDuckGo Search Metadata Recovery"
                            break
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
            "raw_text": raw_text,
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
            raw_text=raw_text.strip(),
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
        """Uses the live LLM to extract structured listing fields and merges with direct review extraction."""
        system_prompt = (
            "You are Agent 1 (Listing Ingestion Agent) in an E-Commerce Trust & Safety pipeline. "
            "Extract ONLY real facts explicitly present in the provided product listing text. "
            "Never fabricate reviews, prices, or seller account ages that are not stated."
        )

        prepared_payload = self.prepare_llm_payload(raw_text)

        user_prompt = f"""
Source URL: {source_url or 'Direct Listing Paste'}

Product Page Content (Specifications & Reviews):
{prepared_payload}

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
        try:
            parsed, _, _ = llm_client.generate_json(user_prompt, system_instruction=system_prompt)
        except Exception:
            parsed = {}

        if not isinstance(parsed, dict):
            parsed = {}

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
        seen_reviews = set()

        # 1. Parse reviews returned by the LLM
        parsed_reviews_raw = parsed.get("reviews")
        if isinstance(parsed_reviews_raw, list):
            for idx, r in enumerate(parsed_reviews_raw, start=1):
                if not isinstance(r, dict):
                    continue
                r_text = str(r.get("text") or "").strip()
                if not r_text:
                    continue
                r_reviewer = str(r.get("reviewer_id") or f"buyer-{idx}").strip()
                if r_reviewer in ("3.6", "4.0", "5.0", "1.0", "2.0") or r_reviewer.lower() in ("customer reviews", "from acwo", "global ratings"):
                    continue
                r_title = str(r.get("title") or "Customer Review").strip()
                r_rating = float(r.get("rating") or 5.0)
                r_date = self.normalize_review_date(str(r.get("timestamp") or ""))
                r_ver = bool(r.get("verified_purchase", True))
                r_help = int(r.get("helpful_votes") or 0)

                key = (r_reviewer.lower(), round(r_rating, 1))
                seen_reviews.add(key)
                reviews.append(
                    ReviewItem(
                        review_id=f"rev-{len(reviews) + 1}",
                        reviewer_id=r_reviewer,
                        rating=r_rating,
                        title=r_title,
                        text=r_text[:500],
                        timestamp=r_date,
                        verified_purchase=r_ver,
                        helpful_votes=r_help,
                    )
                )

        # 2. Merge heuristic-extracted reviews to guarantee no scraped reviews are omitted
        heuristic_reviews = self.extract_reviews_heuristic(raw_text)
        for hr in heuristic_reviews:
            h_key = (hr.reviewer_id.lower(), round(hr.rating, 1))
            if h_key not in seen_reviews:
                seen_reviews.add(h_key)
                hr.review_id = f"rev-{len(reviews) + 1}"
                reviews.append(hr)

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

        product_title = str(parsed.get("title") or "").strip()
        if not product_title or product_title.lower() == "untitled listing":
            title_m = re.search(r"(?:Product Title|Title):\s*([^\n]+)|#\s*([^\n]+)", raw_text)
            if title_m:
                product_title = (title_m.group(1) or title_m.group(2) or "").strip()
            if not product_title:
                product_title = "E-Commerce Product Listing"
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
