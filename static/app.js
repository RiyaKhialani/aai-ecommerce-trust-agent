// State
let currentEngineMode = "llm";
let lastReport = null;

const AGENT_ICONS = {
  1: "📦", 2: "📊", 3: "⚖️", 4: "📑", 5: "🕵️",
  6: "🏢", 7: "🖼️", 8: "🧮", 9: "📝", 10: "🎯"
};

const BENCHMARK_URLS = {
  rhode_live: "https://www.amazon.in/Hydrating-Buildable-Moisturising-Non-Sticky-ESPRESSO/dp/B0GRCVYQ68",
  ultracharge_fraud: "ultracharge_fraud",
  miracle_supplement: "miracle_supplement",
  genuine_audio: "genuine_audio"
};

document.addEventListener("DOMContentLoaded", () => {
  renderInitialStepper();
  loadCategoryRadar();
  if (window.PRELOADED_REPORT) {
    lastReport = window.PRELOADED_REPORT;
    renderVisualDashboard(window.PRELOADED_REPORT);
    const urlInput = document.getElementById("product-url-input");
    if (urlInput && window.PRELOADED_REPORT.product_name) {
      urlInput.value = window.PRELOADED_REPORT.product_name;
    }
    const params = new URLSearchParams(window.location.search);
    const t = params.get("tab");
    if (t) {
      setTimeout(() => switchVisualTab(`tab-${t}`), 50);
    }
  }
});

function setEngineMode(mode) {
  currentEngineMode = mode;
  const demoBtn = document.getElementById("btn-engine-demo");
  const llmBtn = document.getElementById("btn-engine-llm");
  const modeText = document.getElementById("engine-mode-text");

  if (mode === "demo") {
    demoBtn.classList.add("active");
    llmBtn.classList.remove("active");
    modeText.textContent = "Demo Engine (Reproducible)";
    modeText.style.color = "#38bdf8";
  } else {
    llmBtn.classList.add("active");
    demoBtn.classList.remove("active");
    modeText.textContent = "Live AI LLM Inference";
    modeText.style.color = "#a855f7";
  }
}

function loadBenchmarkPreset(key) {
  const input = document.getElementById("product-url-input");
  input.value = BENCHMARK_URLS[key] || key;
  executeTrustPipeline();
}

function renderInitialStepper() {
  const track = document.getElementById("agent-stepper-track");
  if (!track) return;

  const agentNames = [
    "Listing Ingestion", "Review Segmentation", "Policy Compliance",
    "Claim Extraction", "Review Authenticity", "Seller Profiling",
    "Image & Brand", "Risk Aggregation", "Executive Report", "Orchestrator"
  ];

  track.innerHTML = agentNames.map((name, i) => `
    <div class="step-card" id="step-${i+1}">
      <div class="step-info">
        <span class="step-icon">${AGENT_ICONS[i+1]}</span>
        <span class="step-name">${name}</span>
      </div>
      <span class="step-time" id="time-${i+1}">--</span>
    </div>
  `).join("");
}

async function executeTrustPipeline() {
  const inputVal = document.getElementById("product-url-input").value.trim();
  const btn = document.getElementById("run-audit-btn");
  const timer = document.getElementById("total-pipeline-timer");

  if (!inputVal) {
    alert("Please enter a product URL or select a benchmark preset.");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Auditing...</span>`;
  timer.textContent = "Pipeline executing...";

  // Reset steps
  for (let i = 1; i <= 10; i++) {
    const el = document.getElementById(`step-${i}`);
    if (el) el.className = "step-card active";
  }

  const isBench = ["ultracharge_fraud", "miracle_supplement", "genuine_audio"].includes(inputVal);
  const payload = {
    target: inputVal,
    input_mode: isBench ? "benchmark" : "live_url",
    engine_mode: currentEngineMode
  };

  try {
    const res = await fetch("/api/analyze-trust", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (!result.ok) {
      alert("Audit error: " + result.error);
      return;
    }

    lastReport = result.data;
    renderVisualDashboard(result.data);
  } catch (err) {
    alert("Request failed: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡ Audit Listing</span>`;
  }
}

function renderVisualDashboard(report) {
  document.getElementById("results-view").classList.remove("hidden");

  // 1. Update Stepper with realistic timings
  if (report.agent_timeline) {
    let totalTime = 0;
    report.agent_timeline.forEach(a => {
      totalTime += a.execution_time_ms;
      const el = document.getElementById(`step-${a.agent_id}`);
      const t = document.getElementById(`time-${a.agent_id}`);
      if (t) t.textContent = `${a.execution_time_ms.toFixed(1)} ms`;
      if (el) {
        if (report.overall_trust_score < 50 && (a.agent_id === 3 || a.agent_id === 5 || a.agent_id === 6 || a.agent_id === 7)) {
          el.className = "step-card flagged";
        } else {
          el.className = "step-card verified";
        }
      }
    });
    document.getElementById("total-pipeline-timer").textContent = `${totalTime.toFixed(1)} ms across 10 agents`;
  }

  // 2. Score Hero
  const score = report.overall_trust_score;
  const scoreValEl = document.getElementById("score-val");
  scoreValEl.textContent = Math.round(score);

  const gaugeBar = document.getElementById("gauge-circle-bar");
  const riskBadge = document.getElementById("risk-tier-badge");
  const verdictBanner = document.getElementById("verdict-banner");
  const verdictIcon = document.getElementById("verdict-icon");

  // SVG Circumference = 2 * pi * 50 = ~314
  const offset = 314 - (score / 100) * 314;
  gaugeBar.style.strokeDashoffset = offset;

  if (score < 50) {
    gaugeBar.style.stroke = "var(--risk-high)";
    scoreValEl.style.color = "var(--risk-high)";
    riskBadge.className = "risk-pill-badge";
    riskBadge.style.background = "var(--risk-high-bg)";
    riskBadge.style.color = "var(--risk-high)";
    riskBadge.style.borderColor = "rgba(244, 63, 94, 0.4)";
    riskBadge.textContent = "CRITICAL RISK";
    verdictBanner.style.borderLeftColor = "var(--risk-high)";
    verdictIcon.textContent = "🚨";
  } else if (score < 75) {
    gaugeBar.style.stroke = "var(--risk-med)";
    scoreValEl.style.color = "var(--risk-med)";
    riskBadge.className = "risk-pill-badge";
    riskBadge.style.background = "var(--risk-med-bg)";
    riskBadge.style.color = "var(--risk-med)";
    riskBadge.style.borderColor = "rgba(251, 191, 36, 0.4)";
    riskBadge.textContent = "MEDIUM RISK";
    verdictBanner.style.borderLeftColor = "var(--risk-med)";
    verdictIcon.textContent = "⚠️";
  } else {
    gaugeBar.style.stroke = "var(--risk-low)";
    scoreValEl.style.color = "var(--risk-low)";
    riskBadge.className = "risk-pill-badge";
    riskBadge.style.background = "var(--risk-low-bg)";
    riskBadge.style.color = "var(--risk-low)";
    riskBadge.style.borderColor = "rgba(16, 185, 129, 0.4)";
    riskBadge.textContent = "AUTHENTIC (LOW RISK)";
    verdictBanner.style.borderLeftColor = "var(--risk-low)";
    verdictIcon.textContent = "✅";
  }

  document.getElementById("hero-title").textContent = report.product_name;
  document.getElementById("hero-seller-line").textContent = `Seller: ${report.seller_name} | Category: ${report.category}`;
  document.getElementById("verdict-title").textContent = report.recommended_verdict;
  document.getElementById("verdict-summary").textContent = report.executive_summary;

  // Visual Flag Chips
  const flagsContainer = document.getElementById("flag-chips");
  const chips = [];
  if (report.overall_trust_score < 50) {
    chips.push(`<span class="flag-chip critical">🚨 Counterfeit Signals</span>`);
  }
  if (report.authenticity_score < 0.3) {
    chips.push(`<span class="flag-chip critical">❌ Fake Product Complaints</span>`);
  }
  if (report.seller_score < 0.4) {
    chips.push(`<span class="flag-chip warning">📉 Suspicious Price Dump</span>`);
  }
  if (report.compliance_score < 0.5) {
    chips.push(`<span class="flag-chip warning">⚖️ Catalog Policy Breaches</span>`);
  }
  if (report.image_integrity_score < 0.5) {
    chips.push(`<span class="flag-chip warning">📸 Packaging Flaws Reported</span>`);
  }
  if (chips.length === 0) {
    chips.push(`<span class="flag-chip neutral">🛡️ Verified Brand Placement</span>`);
    chips.push(`<span class="flag-chip neutral">✅ Organic Review Curve</span>`);
  }
  flagsContainer.innerHTML = chips.join("");

  // 3. Component Gauges
  const updateBar = (valId, fillId, val) => {
    const pct = Math.round(val * 100);
    document.getElementById(valId).textContent = `${pct}%`;
    const f = document.getElementById(fillId);
    f.style.width = `${pct}%`;
    if (pct < 40) f.style.background = "var(--risk-high)";
    else if (pct < 75) f.style.background = "var(--risk-med)";
    else f.style.background = "var(--risk-low)";
  };

  updateBar("comp-compliance-val", "fill-compliance", report.compliance_score);
  updateBar("comp-auth-val", "fill-auth", report.authenticity_score);
  updateBar("comp-seller-val", "fill-seller", report.seller_score);
  updateBar("comp-image-val", "fill-image", report.image_integrity_score);

  // 4. Tab 1: Key Risks Visual Cards
  const riskGrid = document.getElementById("risk-cards-grid");
  riskGrid.innerHTML = (report.itemized_evidence || []).map(ev => {
    const isCrit = ev.risk_level.toLowerCase() === "critical" || ev.risk_level.toLowerCase() === "high";
    const cardClass = isCrit ? "critical" : (ev.risk_level.toLowerCase() === "medium" ? "warning" : "low");
    const tagBg = isCrit ? "rgba(244, 63, 94, 0.2)" : (cardClass === "warning" ? "rgba(251, 191, 36, 0.2)" : "rgba(16, 185, 129, 0.2)");
    const tagColor = isCrit ? "var(--risk-high)" : (cardClass === "warning" ? "var(--risk-med)" : "var(--risk-low)");

    return `
      <div class="risk-item-card ${cardClass}">
        <div class="risk-card-top">
          <span class="risk-card-module">${ev.module}</span>
          <span class="risk-level-tag" style="background: ${tagBg}; color: ${tagColor}">${ev.risk_level.toUpperCase()}</span>
        </div>
        <div class="risk-card-title">${ev.item_detected}</div>
        <p class="risk-card-body">${ev.explanation}</p>
        <div class="risk-card-action">Action: ${ev.recommendation}</div>
      </div>
    `;
  }).join("");

  // 5. Tab 2: Buyer Reviews Callouts
  const reviewsGrid = document.getElementById("reviews-callouts-grid");
  if (report.duplicate_phrases_found && report.duplicate_phrases_found.length > 0) {
    reviewsGrid.innerHTML = report.duplicate_phrases_found.map(p => `
      <div class="buyer-callout-card">
        <div class="callout-top">
          <span class="star-badge">⚠️ TEMPLATE BOT BURST</span>
          <span class="callout-title">Repeated Phrase: "${p.phrase}"</span>
        </div>
        <p class="callout-text">Identical boilerplate phrasing found in ${p.count} separate customer reviews.</p>
        <span class="callout-meta">Cluster Pattern: ${p.cluster_type}</span>
      </div>
    `).join("");
  } else {
    // Show direct feedback or clean note
    const directReview = (report.itemized_evidence || []).find(e => e.module.includes("Direct Buyer") || e.explanation.includes("Fake product"));
    if (directReview) {
      reviewsGrid.innerHTML = `
        <div class="buyer-callout-card">
          <div class="callout-top">
            <span class="star-badge">1.0★ VERIFIED BUYER ALERT</span>
            <span class="callout-title">${directReview.item_detected}</span>
          </div>
          <p class="callout-text">"${directReview.explanation}"</p>
          <span class="callout-meta">Direct Buyer Counterfeit Complaint</span>
        </div>
      `;
    } else {
      reviewsGrid.innerHTML = `<p style="font-size: 13px; color: var(--text-dim); padding: 12px;">Customer reviews indicate organic sentiment distribution with no coordinated phrasing rings.</p>`;
    }
  }

  // 6. Tab 3: Price & Packaging Diff
  const specsDiff = document.getElementById("specs-diff-view");
  let priceDumpHtml = "";
  if (report.seller_flags && report.seller_flags.some(f => f.includes("Crash") || f.includes("markdown") || f.includes("drop"))) {
    priceDumpHtml = `
      <div class="spec-diff-card">
        <div class="diff-title">📉 Suspicious Price Dumping Anomaly</div>
        <p style="font-size: 12px; color: var(--text-muted)">Massive price slash preceding listing clearance:</p>
        <div class="price-compare-row">
          <span class="mrp-strike">M.R.P. Baseline</span>
          <span class="sale-price">Current Listing</span>
          <span class="dump-badge">🔥 MASSIVE DUMP</span>
        </div>
      </div>
    `;
  }

  let packagingHtml = "";
  if (report.image_flags && report.image_flags.length > 0) {
    packagingHtml = `
      <div class="spec-diff-card">
        <div class="diff-title">📸 Packaging & Visual Discrepancies</div>
        ${report.image_flags.map(f => `<p style="font-size: 12px; color: #fb7185; margin-bottom: 6px;">⚠️ ${f}</p>`).join("")}
      </div>
    `;
  }

  specsDiff.innerHTML = (priceDumpHtml + packagingHtml) || `<p style="font-size: 13px; color: var(--text-dim); padding: 12px;">No price dumps or packaging defects flagged.</p>`;

  // 7. Tab 4: Redlines
  const redlinesView = document.getElementById("redlines-view");
  if (report.redline_suggestions && report.redline_suggestions.length > 0) {
    redlinesView.innerHTML = report.redline_suggestions.map(r => `
      <div class="spec-diff-card" style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #fb7185;">Policy Breach Detected</span>
          <span style="font-size: 11px; color: var(--text-dim);">${r.reason || "Catalog Compliance"}</span>
        </div>
        <div style="text-decoration: line-through; color: #fb7185; font-size: 13px; margin-bottom: 6px;">
          ❌ "${r.original}"
        </div>
        <div style="color: #34d399; font-size: 13px; font-weight: 600;">
          ✅ "${r.compliant_replacement}"
        </div>
      </div>
    `).join("");
  } else {
    redlinesView.innerHTML = `<p style="font-size: 13px; color: var(--text-dim); padding: 12px;">All extracted specifications comply with marketplace listing standards.</p>`;
  }

  // 8. Tab 5: Auto Seller Notice
  const noticeBox = document.getElementById("notice-textarea");
  noticeBox.value = report.auto_suggested_reviewer_prompt || "No inquiry required.";

  // 9. Tab 6: Verbose Audit Logs (Gemini 3.8 Flash & Agents)
  const auditLogsView = document.getElementById("audit-logs-view");
  if (report.verbose_audit_logs && report.verbose_audit_logs.length > 0) {
    auditLogsView.innerHTML = report.verbose_audit_logs.map(log => `
      <div class="spec-diff-card" style="margin-bottom: 10px; border-left: 3px solid ${log.event_type.includes('LLM') ? '#a855f7' : '#38bdf8'};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <div>
            <span style="font-weight: 700; font-size: 13px; color: #f8fafc;">Agent ${log.agent_id}: ${log.agent_name}</span>
            <span class="pill-chip" style="font-size: 10px; margin-left: 8px; color: ${log.event_type.includes('LLM') ? '#c084fc' : '#38bdf8'}; border-color: ${log.event_type.includes('LLM') ? 'rgba(192,132,252,0.3)' : 'rgba(56,189,248,0.3)'};">
              ${log.event_type}
            </span>
          </div>
          <span style="font-size: 11px; font-family: monospace; color: var(--text-dim);">${log.timestamp}</span>
        </div>
        <pre style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 6px; font-size: 11px; font-family: monospace; color: #94a3b8; overflow-x: auto; white-space: pre-wrap; margin: 0;">${JSON.stringify(log.data, null, 2)}</pre>
      </div>
    `).join("");
  } else {
    auditLogsView.innerHTML = `<p style="font-size: 13px; color: var(--text-dim); padding: 12px;">No verbose audit records captured.</p>`;
  }

  // Scroll to results smoothly
  document.getElementById("results-view").scrollIntoView({ behavior: "smooth" });
}

function switchVisualTab(tabId) {
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-pane-view").forEach(p => p.classList.add("hidden"));

  const targetTab = Array.from(document.querySelectorAll(".nav-tab")).find(t => t.getAttribute("onclick").includes(tabId));
  if (targetTab) targetTab.classList.add("active");

  const pane = document.getElementById(`pane-${tabId}`);
  if (pane) pane.classList.remove("hidden");
}

function copyNoticeText() {
  const t = document.getElementById("notice-textarea").value;
  navigator.clipboard.writeText(t).then(() => alert("Notice copied to clipboard!"));
}

async function loadCategoryRadar() {
  try {
    const res = await fetch("/api/category-analytics");
    const data = await res.json();
    const container = document.getElementById("category-bars-grid");
    if (!container || !data.categories) return;

    container.innerHTML = data.categories.map(c => `
      <div class="cat-stat-box">
        <div class="cat-stat-title">${c.name}</div>
        <div class="cat-stat-score" style="color: ${c.avg_trust_score < 50 ? 'var(--risk-high)' : (c.avg_trust_score < 75 ? 'var(--risk-med)' : 'var(--risk-low)')}">
          ${c.avg_trust_score} / 100
        </div>
        <div class="cat-stat-sub">Fraud Density: <strong>${c.fraud_density}</strong> (${c.audited_count} audited items)</div>
      </div>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}
