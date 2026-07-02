import {
  brief as mockBrief,
  dashboardAnalysis,
  evidenceItems,
  riskItems,
} from "../data/mockAnalysis.js";

function clampPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  const percent = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(percent)));
}

function riskSeverityToStatus(severity) {
  const normalized = String(severity || "").toLowerCase();
  if (normalized === "high" || normalized === "critical") return "High";
  if (normalized === "low") return "Low";
  return "Medium";
}

export function normalizeJobToAnalysis(job) {
  const data = job?.result?.data || {};
  const consistency = clampPercent(data.consistency_score);
  const title = job?.ticker ? `${job.ticker} · Q2 2026` : "AMD · Q2 2026";
  const risks = Array.isArray(data.risk_factors) ? data.risk_factors : [];
  const comparisons = Array.isArray(data.slide_speech_comparison)
    ? data.slide_speech_comparison
    : [];

  const mappedRisks = risks.length
    ? risks.map((risk, index) => ({
        count: String(index + 1).padStart(2, "0"),
        label: risk.label || "Detected Risk",
        severity: riskSeverityToStatus(risk.severity),
        description: risk.description || "Backend analysis flagged this item for review.",
      }))
    : riskItems;

  const mappedEvidence = comparisons.length
    ? comparisons.map((item, index) => ({
        id: `backend-evidence-${index}`,
        claim: item.slide_metric || `Backend comparison ${index + 1}`,
        status: item.status === "reviewed" ? "Verified" : "Needs Review",
        confidence: consistency || 78,
        source: "Slide vs Speech",
        snippet: item.speech_reference || "No transcript excerpt available.",
        location: `Comparison ${index + 1}`,
      }))
    : evidenceItems;

  const mappedBrief = {
    ...mockBrief,
    preview: data.executive_summary || mockBrief.preview,
    sections: data.full_report
      ? [
          {
            title: "Generated Report",
            body: data.full_report.replace(/^#\s.+\n*/m, "").trim(),
          },
        ]
      : mockBrief.sections,
  };

  return {
    dashboard: {
      ...dashboardAnalysis,
      ticker: job?.ticker || dashboardAnalysis.ticker,
      company: job?.ticker || dashboardAnalysis.company,
      period: title.split("·")[1]?.trim() || dashboardAnalysis.period,
      status:
        job?.status === "completed"
          ? `Completed ${job.completed_at ? "from backend" : ""}`.trim()
          : dashboardAnalysis.status,
      summary: data.executive_summary || dashboardAnalysis.summary,
      metrics: dashboardAnalysis.metrics.map((metric) =>
        metric.label === "Consistency Score" && consistency
          ? { ...metric, value: String(consistency), detail: "Mapped from backend consistency score." }
          : metric
      ),
    },
    risks: mappedRisks,
    evidence: mappedEvidence,
    brief: mappedBrief,
  };
}
