/**
 * Mock / fallback data for the MEIA earnings-intelligence dashboard.
 *
 * Every named export here is consumed by src/services/analysisService.js
 * and/or src/services/backendAdapter.js.  When the backend returns real
 * results they override these values; otherwise the UI renders the
 * fixtures below so the dashboard is never empty.
 */

// ---------------------------------------------------------------------------
// Dashboard analysis  (AnalysisHeader, SummaryCard, MetricCard, TrendPanel)
// ---------------------------------------------------------------------------
export const dashboardAnalysis = {
  ticker: "AMD",
  company: "AMD",
  period: "Q2 2026",
  status: "Verified · Live",

  // SummaryCard
  headline: "Consistent Earnings Signal",
  summary:
    "AMD's Q2 2026 earnings call shows strong alignment between management commentary and filed financials. Revenue guidance reiterated at $6.8 B with data-center segment up 18 % QoQ.",
  checklist: [
    "Audio-slide alignment verified",
    "Revenue figures cross-referenced with 10-Q",
    "Risk factors flagged and scored",
    "Executive summary generated",
  ],

  // MetricCard grid — each item must have label, value, detail, delta, tone, suffix, title
  metrics: [
    { label: "Consistency Score", value: "92", suffix: "%", title: "Audio vs Slides", detail: "3 pp above sector avg", delta: "+3 pp", tone: "positive" },
    { label: "Claims Verified", value: "47", suffix: "/54", title: "Cross-Ref Claims", detail: "87 % verification rate", delta: "+6", tone: "positive" },
    { label: "Risk Flags", value: "3", suffix: "", title: "Flagged Items", detail: "Down from 5 last quarter", delta: "−2", tone: "positive" },
    { label: "Confidence", value: "88", suffix: "%", title: "Model Confidence", detail: "Weighted across all agents", delta: "+1 pp", tone: "positive" },
    { label: "Sources Processed", value: "5", suffix: "", title: "Ingested Sources", detail: "Audio, slides, 10-Q, 8-K, transcript", delta: "", tone: "neutral" },
  ],

  // TrendPanel
  trendSummary: [
    { label: "Consistency", value: "92 %", previous: "prev 89 %", delta: "+3 pp" },
    { label: "Risk Flags", value: "3", previous: "prev 5", delta: "−2" },
    { label: "Verified Claims", value: "47", previous: "prev 41", delta: "+6" },
  ],
  chart: [
    { label: "Q1 25", consistency: 85, riskFlags: 7, verifiedClaims: 34 },
    { label: "Q2 25", consistency: 89, riskFlags: 5, verifiedClaims: 41 },
    { label: "Q3 25", consistency: 92, riskFlags: 3, verifiedClaims: 47 },
  ],
};

// ---------------------------------------------------------------------------
// Agent statuses  (AgentStatusCard)
//   Each agent needs: title, subtitle, icon, messages[{text, severity}]
// ---------------------------------------------------------------------------
export const agentStatuses = [
  {
    title: "ASR Agent",
    subtitle: "Speech-to-text transcription",
    icon: "mic",
    messages: [
      { severity: "info", text: "Audio loaded — 42 min, 16 kHz stereo" },
      { severity: "ok", text: "Diarization complete — 3 speakers detected" },
      { severity: "ok", text: "Transcription finished — WER 4.2 %" },
    ],
  },
  {
    title: "Vision Agent",
    subtitle: "Slide deck extraction",
    icon: "layers",
    messages: [
      { severity: "info", text: "PDF parsed — 48 slides identified" },
      { severity: "ok", text: "OCR accuracy 97 %" },
      { severity: "warn", text: "Slide 32 — low contrast, manual review suggested" },
    ],
  },
  {
    title: "Filing Agent",
    subtitle: "SEC filing ingestion",
    icon: "shield",
    messages: [
      { severity: "info", text: "10-Q and 8-K fetched from EDGAR" },
      { severity: "ok", text: "Financial tables extracted — 14 tables" },
      { severity: "ok", text: "KPIs mapped to management claims" },
    ],
  },
  {
    title: "Orchestrator",
    subtitle: "Cross-verification & report gen",
    icon: "shield",
    messages: [
      { severity: "info", text: "All agents completed — starting merge" },
      { severity: "ok", text: "47 / 54 claims verified" },
      { severity: "ok", text: "Report generated — 3 risk flags" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Data-quality metrics  (DataQualityCard)
//   Expects: score, transcriptScore, transcriptBadge,
//            metrics (array of [label, value] tuples),
//            stats   (array of [label, value] tuples)
// ---------------------------------------------------------------------------
export const qualityMetrics = {
  score: 94,
  transcriptScore: "96 %",
  transcriptBadge: "High Fidelity",
  metrics: [
    ["Audio Quality", "94 %"],
    ["Slide OCR Accuracy", "97 %"],
    ["Filing Parse Rate", "100 %"],
    ["Transcript WER", "4.2 %"],
  ],
  stats: [
    ["Audio Duration", "42 min"],
    ["Slides Processed", "48"],
    ["Filing Pages", "124"],
    ["Transcript Words", "11,430"],
    ["Claims Extracted", "54"],
    ["Evidence Links", "127"],
  ],
};

// ---------------------------------------------------------------------------
// Risk items  (RiskMonitor, backendAdapter fallback)
//   Each: count, label, severity, description
// ---------------------------------------------------------------------------
export const riskItems = [
  {
    count: "01",
    label: "Revenue Guidance Gap",
    severity: "High",
    description:
      "Management's verbal guidance of $6.8 B exceeds the 10-Q midpoint by $200 M. Warrants scrutiny of segment-level assumptions.",
  },
  {
    count: "02",
    label: "Inventory Build-Up",
    severity: "Medium",
    description:
      "Channel inventory rose 12 % QoQ while sell-through grew only 6 %. Potential over-shipping risk flagged.",
  },
  {
    count: "03",
    label: "Hedging Language Detected",
    severity: "Low",
    description:
      'CEO used qualifying phrases ("subject to", "preliminary") 14 times — above the sector median of 8.',
  },
];

// ---------------------------------------------------------------------------
// Evidence / claim items  (EvidencePage, ClaimsPage, ClaimVerificationPreview)
//   Each: id, claim, status, confidence, source, snippet, location
// ---------------------------------------------------------------------------
export const evidenceItems = [
  {
    id: "ev-1",
    claim: "Data-center revenue up 18 % QoQ",
    status: "Verified",
    confidence: 94,
    source: "10-Q Filing",
    snippet: "Data Center segment revenue of $2.6 B increased 18 % sequentially.",
    location: "10-Q p. 12",
  },
  {
    id: "ev-2",
    claim: "Gross margin expanded to 54 %",
    status: "Verified",
    confidence: 91,
    source: "Earnings Transcript",
    snippet: "Non-GAAP gross margin of 54 %, up 200 basis points year-over-year.",
    location: "Transcript L. 204",
  },
  {
    id: "ev-3",
    claim: "Client segment grew 10 % YoY",
    status: "Needs Review",
    confidence: 72,
    source: "Slide Deck",
    snippet: "Client revenue growth driven by Ryzen 9000 ramp.",
    location: "Slide 18",
  },
  {
    id: "ev-4",
    claim: "AI accelerator TAM of $150 B by 2027",
    status: "Needs Review",
    confidence: 65,
    source: "Earnings Transcript",
    snippet: "We see the AI accelerator TAM reaching $150 B by calendar 2027.",
    location: "Transcript L. 87",
  },
  {
    id: "ev-5",
    claim: "Embedded segment operating income flat",
    status: "Unsupported",
    confidence: 48,
    source: "10-Q Filing",
    snippet: "Embedded operating income declined 3 % QoQ per filing data.",
    location: "10-Q p. 24",
  },
  {
    id: "ev-6",
    claim: "Share buyback of $1.5 B authorized",
    status: "Verified",
    confidence: 98,
    source: "8-K Filing",
    snippet: "Board authorized an additional $1.5 B common stock repurchase program.",
    location: "8-K Exhibit 99.1",
  },
];

// ---------------------------------------------------------------------------
// Analyst brief  (BriefPage, AnalystBriefPreview)
//   Needs: preview, sections[{title, body}], risks[], citationsList[],
//          generated, pages, citations (metadata for AnalystBriefPreview)
// ---------------------------------------------------------------------------
export const brief = {
  company: "AMD",
  period: "Q2 2026",
  preview:
    "AMD delivered a consistent Q2 2026 earnings call with strong data-center momentum and verified revenue claims. Three risk flags warrant monitoring, but overall signal confidence remains high at 88 %.",
  generated: "Jul 9, 2026 · 03:41 UTC",
  pages: 4,
  citations: 6,
  sections: [
    {
      title: "Executive Summary",
      body: "AMD reported Q2 2026 revenue of $6.8 B, up 11 % year-over-year. Data-center was the standout segment at +18 % QoQ, driven by MI400 accelerator demand. Gross margins expanded to 54 % (non-GAAP). Management guidance aligned with filed figures except for a $200 M gap at the top end of revenue guidance.",
    },
    {
      title: "Verification Highlights",
      body: "47 of 54 management claims were verified against SEC filings and the earnings transcript. Audio-to-slide consistency scored 92 %, above the sector average of 86 %. Three risk flags were identified: a revenue guidance gap, an inventory build-up signal, and elevated hedging language.",
    },
    {
      title: "Segment Analysis",
      body: "Data Center ($2.6 B) led growth with MI400 shipments ramping. Client ($1.8 B) grew 10 % YoY on Ryzen 9000 adoption. Gaming ($0.4 B) declined 8 % as console refresh timing weighs. Embedded ($0.9 B) was roughly flat with margin pressure from automotive softness.",
    },
  ],
  risks: [
    "Revenue guidance gap of $200 M above 10-Q midpoint",
    "Channel inventory build-up outpacing sell-through by 6 pp",
    "Elevated hedging language (14 instances vs 8 sector median)",
  ],
  citationsList: [
    "10-Q p. 12 — Data Center revenue",
    "10-Q p. 24 — Embedded segment",
    "8-K Exhibit 99.1 — Buyback authorization",
    "Transcript L. 87 — TAM estimate",
    "Transcript L. 204 — Gross margin commentary",
    "Slide 18 — Client segment growth",
  ],
};

// ---------------------------------------------------------------------------
// Processing-pipeline steps  (ProcessingPage)
//   Each: id, title, description, duration
// ---------------------------------------------------------------------------
export const processingSteps = [
  {
    id: "ingest",
    title: "Source Ingestion",
    description: "Upload and validate audio, slides, and SEC filings.",
    duration: "~30 s",
  },
  {
    id: "asr",
    title: "Audio Transcription",
    description: "Speech-to-text via ASR agent with speaker diarization.",
    duration: "~2 min",
  },
  {
    id: "vision",
    title: "Slide Extraction",
    description: "OCR and layout parsing of the earnings slide deck.",
    duration: "~45 s",
  },
  {
    id: "filing",
    title: "Filing Analysis",
    description: "Parse 10-Q and 8-K for KPIs and financial tables.",
    duration: "~20 s",
  },
  {
    id: "kpis",
    title: "KPI Cross-Check",
    description: "Compare management claims with filed figures.",
    duration: "~15 s",
  },
  {
    id: "claims",
    title: "Claim Verification",
    description: "Score each claim against evidence across all sources.",
    duration: "~25 s",
  },
  {
    id: "report",
    title: "Report Generation",
    description: "Compile analyst brief, risk monitor, and evidence room.",
    duration: "~10 s",
  },
];
