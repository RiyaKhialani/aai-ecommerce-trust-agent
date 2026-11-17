"""
Benchmark Datasets for E-commerce Trust Intelligence System.
Includes realistic fraud scenarios (review burst, unverified claims, seller churn)
and genuine baselines for reproducible evaluation, viva demos, and offline testing.
"""

from typing import List, Dict, Any
from agents.schemas import ProductListing, ReviewItem


def get_benchmark_listings() -> Dict[str, ProductListing]:
    # 1. UltraCharge Pro (PS-11 Scenario: High Fraud Burst)
    ultracharge_reviews: List[ReviewItem] = []
    
    # Week 1: Organic baseline (15 reviews)
    for i in range(15):
        ultracharge_reviews.append(
            ReviewItem(
                review_id=f"rev-w1-{i+1}",
                reviewer_id=f"user-base-{i+1}",
                rating=4.0 if i % 2 == 0 else 5.0,
                title="Decent power bank",
                text="Build quality is fine. Charges my phone reasonably well over USB-C.",
                timestamp="2026-09-15T10:00:00Z",
                verified_purchase=True,
                helpful_votes=2,
            )
        )

    # Week 2: Velocity Spike (210 reviews in 48 hours, burst manipulation)
    burst_templates = [
        ("Changed my life!", "Absolutely changed my life, arrived fast and works like magic!"),
        ("Arrived fast best quality", "Arrived fast! Best quality power bank ever bought. Highly recommended!"),
        ("Must buy product", "Must buy product for everyone. Amazing battery backup and arrived fast."),
        ("Superb performance", "Changed my life completely. Best purchase of this year, fast shipping."),
    ]
    for i in range(210):
        tmpl = burst_templates[i % len(burst_templates)]
        ultracharge_reviews.append(
            ReviewItem(
                review_id=f"rev-spike-{i+1}",
                reviewer_id=f"bot-user-{1000 + i}",
                rating=5.0,
                title=tmpl[0],
                text=tmpl[1],
                timestamp="2026-09-22T14:30:00Z",
                verified_purchase=(i % 10 == 0),  # 90% unverified
                helpful_votes=0,
            )
        )

    # Week 3: Post-spike reviews (115 reviews)
    for i in range(115):
        ultracharge_reviews.append(
            ReviewItem(
                review_id=f"rev-w3-{i+1}",
                reviewer_id=f"user-w3-{i+1}",
                rating=5.0 if i % 3 != 0 else 1.0,
                title="Quick charge test" if i % 3 != 0 else "Stopped working after 2 days",
                text="Arrived fast and great backup!" if i % 3 != 0 else "Heats up dangerously while charging. Do not buy!",
                timestamp="2026-09-29T12:00:00Z",
                verified_purchase=False,
                helpful_votes=1,
            )
        )

    ultracharge = ProductListing(
        listing_id="BENCHMARK-001",
        title="UltraCharge Pro 20000mAh Power Bank with 65W SuperVOOC Fast Charging",
        description=(
            "UltraCharge Pro 20000mAh High-Capacity Portable Charger. Features military-grade lithium polymer cells, "
            "dual USB-C PD 65W fast charging output, and digital LED display. CE and UL certified, 2-year replacement "
            "warranty. Guaranteed safe for flight travel. FDA compliant materials and surge protection."
        ),
        brand="UltraCharge",
        category="Electronics",
        price=999.0,
        currency="INR",
        seller_id="SELL-9921",
        seller_name="Shenzhen Volt Direct",
        seller_account_age_days=14,  # Flag: brand new seller with 340 reviews
        seller_rating=4.9,
        price_history=[
            {"date": "2026-09-10", "price": 3499.0},
            {"date": "2026-09-18", "price": 2899.0},
            {"date": "2026-09-22", "price": 999.0},  # Sudden crash before spike
        ],
        image_urls=[
            "https://images.unsplash.com/photo-1609592424079-052c9d194557?w=500",
            "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500"
        ],
        listing_date="2026-09-10",
        stock_status="In Stock",
        specs={
            "Capacity": "20000mAh",
            "Output": "65W USB-C PD",
            "Battery Cell": "Lithium Polymer",
            "Weight": "380g",
            "Certifications": "CE, UL Certified",
            "Warranty": "2 Years Replacement"
        },
        reviews=ultracharge_reviews
    )

    # 2. NutriPure Keto Gummies (High Compliance Violation)
    nutripure_reviews: List[ReviewItem] = []
    for i in range(120):
        nutripure_reviews.append(
            ReviewItem(
                review_id=f"rev-keto-{i+1}",
                reviewer_id=f"keto-user-{i+1}",
                rating=5.0 if i < 110 else 1.0,
                title="Miracle weight loss!" if i < 110 else "Did not work at all scam",
                text="Lost 8kg in 10 days without diet! 100% natural and cures fatigue." if i < 110 else "Artificial taste, gave me severe stomach ache. Refused return.",
                timestamp="2026-09-20T18:00:00Z",
                verified_purchase=(i % 5 == 0),
                helpful_votes=0,
            )
        )

    nutripure = ProductListing(
        listing_id="BENCHMARK-002",
        title="NutriPure Miracle Keto Slim Gummies - 100% Organic Fat Burner",
        description=(
            "NutriPure Miracle Keto Gummies are clinically proven to melt 10kg belly fat in 7 days without exercise. "
            "FDA Approved formula, doctor certified, cures metabolic syndrome and diabetes. 100% herbal extracts with zero side effects. "
            "Money back guarantee if you don't lose weight immediately."
        ),
        brand="NutriPure Organics",
        category="Health & Supplements",
        price=1499.0,
        currency="INR",
        seller_id="SELL-4812",
        seller_name="HerbalLife QuickMart",
        seller_account_age_days=25,
        seller_rating=4.7,
        price_history=[
            {"date": "2026-09-01", "price": 2499.0},
            {"date": "2026-09-15", "price": 1499.0},
        ],
        image_urls=["https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500"],
        listing_date="2026-09-01",
        stock_status="In Stock",
        specs={
            "Quantity": "60 Gummies",
            "Dosage": "2 daily",
            "Certifications": "FDA Approved, GMP",
            "Guarantee": "100% Cure"
        },
        reviews=nutripure_reviews
    )

    # 3. AcousticSound Pro ANC Earbuds (Authentic Baseline)
    earbud_reviews: List[ReviewItem] = []
    review_comments = [
        (5.0, "Excellent active noise cancellation for the price", "ANC does a solid job filtering out AC hum and traffic. Battery lasts about 6.5 hours on single charge.", True),
        (4.0, "Great audio clarity, mic could be slightly better", "Bass is punchy without overpowering mids. In windy outdoor calls the mic picks up some noise.", True),
        (5.0, "Comfortable fit for long study sessions", "Ear tips seal well. Pairs instantly with my phone and laptop via multipoint.", True),
        (3.0, "Average latency in fast gaming", "Good for Spotify and YouTube, but noticeable lag in competitive shooter games.", True),
        (2.0, "Right earbud dropped connection once", "Had to reset in charging case to re-pair. Support answered within 24 hours.", True),
        (5.0, "Solid daily drivers", "Used daily on metro commutes for 3 months. Case scratch resistance is good.", True),
    ]
    for i in range(120):
        rating, title, text, verified = review_comments[i % len(review_comments)]
        earbud_reviews.append(
            ReviewItem(
                review_id=f"rev-earbud-{i+1}",
                reviewer_id=f"audio-buyer-{10000 + i}",
                rating=rating,
                title=title,
                text=text,
                timestamp=f"2026-0{1 + (i % 8):02d}-15T12:00:00Z",
                verified_purchase=verified,
                helpful_votes=i % 4,
            )
        )

    earbuds = ProductListing(
        listing_id="BENCHMARK-003",
        title="AcousticSound Pro True Wireless Earbuds with Hybrid Active Noise Cancellation",
        description=(
            "AcousticSound Pro Earbuds deliver crystal clear acoustics with custom 11mm bio-cellulose dynamic drivers. "
            "Features Hybrid Active Noise Cancellation up to 35dB, transparency mode, and 30-hour total playback with USB-C case. "
            "IPX5 water resistance for workouts. BIS certified (R-41002341) with 1-year manufacturer warranty."
        ),
        brand="AcousticSound",
        category="Audio & Accessories",
        price=3299.0,
        currency="INR",
        seller_id="SELL-1049",
        seller_name="AcousticSound Official Retail India",
        seller_account_age_days=780,  # Established seller
        seller_rating=4.8,
        price_history=[
            {"date": "2025-10-01", "price": 3499.0},
            {"date": "2026-01-15", "price": 3299.0},
            {"date": "2026-08-10", "price": 3299.0},
        ],
        image_urls=["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500"],
        listing_date="2025-08-15",
        stock_status="In Stock",
        specs={
            "Driver": "11mm Dynamic",
            "Battery Life": "30 Hours total",
            "Water Resistance": "IPX5",
            "Bluetooth": "5.3",
            "Certifications": "BIS Certified R-41002341, CE",
            "Warranty": "1 Year Official Brand Warranty"
        },
        reviews=earbud_reviews
    )

    # 4. RHODE Peptide Lip Tint (Mirror of Live Amazon ASIN B0GRCVYQ68 — 1,780 Total Reviews)
    # Reflects classic ASIN Hijacking & Listing Drift: 
    # - 1,200 reviews in 2025 (Historical organic generic lip balm baseline, avg 4.2★)
    # - 500 reviews in early 2026 (Continued organic baseline, avg 4.1★)
    # - 80 reviews in late 2026 (Post-hijacking counterfeit wave: seller MECURE GLOBAL swapped ASIN to Rhode Lip Tint,
    #   price dropped 77%, verified buyers receive toxic Indian counterfeits and submit 1.0★ scam/safety alerts)
    rhode_reviews: List[ReviewItem] = []

    # Historical Cohort 1: 2025-01 to 2025-11 (1,200 organic reviews)
    hist_templates = [
        ("Good hydrating balm", "Keeps lips moist for hours. Smooth non-sticky texture, decent everyday lip care.", 4.0),
        ("Nice pleasant flavor", "Subtle fragrance and soft gloss. Good value for money purchase.", 5.0),
        ("Average daily moisturizer", "It is an okay moisturizing balm. Not too shiny, simple packaging.", 4.0),
        ("Decent lip tint", "Gives a faint reddish hue. Re-applied twice a day.", 4.0),
    ]
    for i in range(1200):
        t_title, t_body, t_rate = hist_templates[i % len(hist_templates)]
        rhode_reviews.append(
            ReviewItem(
                review_id=f"rev-rhode-hist1-{i+1}",
                reviewer_id=f"user-legacy-{i+1}",
                rating=t_rate,
                title=t_title,
                text=t_body,
                timestamp="2025-06-15T10:00:00Z",
                verified_purchase=(i % 10 != 0),
                helpful_votes=i % 4
            )
        )

    # Historical Cohort 2: 2026-01 to 2026-07 (500 reviews)
    for i in range(500):
        t_title, t_body, t_rate = hist_templates[i % len(hist_templates)]
        rhode_reviews.append(
            ReviewItem(
                review_id=f"rev-rhode-hist2-{i+1}",
                reviewer_id=f"user-trans-{i+1}",
                rating=t_rate,
                title=t_title,
                text=t_body,
                timestamp="2026-03-20T14:30:00Z",
                verified_purchase=(i % 8 != 0),
                helpful_votes=i % 3
            )
        )

    # Recent Counterfeit Hijack Cohort: 2026-08 to 2026-09 (80 reviews, 1.0★ crash with direct scam warnings)
    counterfeit_complaints = [
        ("Fake product and not safe to use scam product", "Counterfeit product! Packaging typo small e but authentic has big e. Fake product and not safe to use scam product! Smell is chemical and sticky. Complete scam by seller MECURE GLOBAL!"),
        ("Duplicate product scam", "Do not buy this duplicate product. Clearly a fake copy from unverified seller. Origin India when original is made in USA. Do not put this on your lips!"),
        ("Severe burning sensation and lip swelling!", "Chemical smell! My lips swelled up and started itching within 10 minutes of applying this fake Rhode tint. Toxic counterfeit adulteration scam!"),
        ("Fake duplicate copied packaging", "Look at the batch code: it doesn't exist on official Rhode skin portal. Tube font is crooked and product is pure petroleum grease. Total scam!"),
        ("Complete fraud duplicate", "Do not get fooled by the 77% discount! Seller swapped the product. Smells like industrial paint. Fake product and not safe to use scam product!"),
    ]
    for i in range(80):
        c_title, c_text = counterfeit_complaints[i % len(counterfeit_complaints)]
        rhode_reviews.append(
            ReviewItem(
                review_id=f"rev-rhode-fake-{i+1}",
                reviewer_id=f"user-amazon-alert-{i+1}",
                rating=1.0,
                title=c_title,
                text=c_text,
                timestamp="2026-09-22T16:00:00Z",
                verified_purchase=True,
                helpful_votes=14 if i == 0 else (8 if i == 1 else (i % 6 + 1))
            )
        )
    rhode_tint = ProductListing(
        listing_id="B0GRCVYQ68",
        title="RHODE Peptide Lip Tint, Hydrating Tinted Lip Balm, Buildable Creamy Color, Moisturising Non-Sticky, 10ml (ESPRESSO RIBBON SALTY)",
        brand="RHODE",
        category="Beauty & Personal Care",
        description="RHODE Peptide Lip Tint tinted lip balm buildable creamy color moisturising non-sticky 10ml espresso ribbon salty. Authorized Official Importer & Exclusive Distribution. Dermatologist Approved Formula. Origin: India. Seller: MECURE GLOBAL.",
        price=1733.0,
        original_mrp=7500.0,
        currency="INR",
        seller_name="MECURE GLOBAL",
        seller_id="SELLER-MECURE-77",
        seller_account_age_days=18,
        seller_country="India",
        origin_country="India",
        image_urls=[
            "https://m.media-amazon.com/images/I/41sample_rhode.jpg"
        ],
        listing_date="2026-08-10",
        stock_status="In Stock",
        specs={
            "Brand": "RHODE",
            "Item Form": "Balm",
            "Finish Type": "Glossy",
            "Origin": "India",
            "Authentic Brand Origin": "USA"
        },
        reviews=rhode_reviews
    )

    return {
        "ultracharge_fraud": ultracharge,
        "miracle_supplement": nutripure,
        "genuine_audio": earbuds,
        "rhode_fake_tint": rhode_tint,
    }


def get_listing_drift_snapshot(benchmark_id: str) -> Dict[str, Any]:
    """Simulates a 30-day historical snapshot to detect listing drift."""
    if benchmark_id == "rhode_fake_tint":
        return {
            "snapshot_date": "30 days ago",
            "drift_detected": True,
            "severity": "Critical",
            "changes": [
                {
                    "attribute": "Price Dumping",
                    "previous": "₹7,500.00 M.R.P.",
                    "current": "₹1,733.00 (76.9% discount)",
                    "flag": "High clearance price cut typical of counterfeit dumping"
                },
                {
                    "attribute": "Origin Discrepancy",
                    "previous": "Origin: United States (RHODE Official)",
                    "current": "Origin: India (MECURE GLOBAL)",
                    "flag": "Unauthorized regional distributor manufacturing imitation stock"
                }
            ],
            "recommendation": "Brand authorization check and physical packaging authenticity audit."
        }
    if benchmark_id == "ultracharge_fraud":
        return {
            "snapshot_date": "30 days ago (2026-09-06)",
            "drift_detected": True,
            "severity": "High",
            "changes": [
                {
                    "attribute": "Seller Entity Swap",
                    "previous": "VoltKing Global Inc. (Established)",
                    "current": "Shenzhen Volt Direct (Created 14 days ago)",
                    "flag": "High Risk: Listing takeover / Account hijack pattern"
                },
                {
                    "attribute": "Price Drop",
                    "previous": "₹3,499.00",
                    "current": "₹999.00 (71% drop)",
                    "flag": "Suspicious clearance dumping preceding review inflation"
                },
                {
                    "attribute": "Specification Alteration",
                    "previous": "Standard 10000mAh Power Bank (18W)",
                    "current": "UltraCharge Pro 20000mAh 65W SuperVOOC",
                    "flag": "Listing reciclature / Spec inflation without SKU update"
                }
            ],
            "recommendation": "Investigate ASIN hijacking and unverified spec inflation."
        }
    elif benchmark_id == "miracle_supplement":
        return {
            "snapshot_date": "30 days ago (2026-08-25)",
            "drift_detected": True,
            "severity": "Critical",
            "changes": [
                {
                    "attribute": "Medical Claims Added",
                    "previous": "Herbal Daily Energy Chewables",
                    "current": "Cures Diabetes and Melts 10kg in 7 days",
                    "flag": "Prohibited medical disease cure claims added"
                }
            ],
            "recommendation": "Immediate suspension of medical disease treatment keywords."
        }
    else:
        return {
            "snapshot_date": "30 days ago",
            "drift_detected": False,
            "severity": "Low",
            "changes": [],
            "recommendation": "Listing specifications and seller profile remain stable."
        }
