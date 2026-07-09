/**
 * Parse MEIA backend job payloads into frontend dashboard shapes.
 *
 * Backend filing verification items use:
 *   claim_text, claimed_value, evidence_snippet, source_filing, is_consistent, status, confidence
 *
 * Frontend evidence/claims rows expect:
 *   id, claim, status, confidence, source, snippet, location, kind
 */

export function clampPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  const percent = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(percent)));
}

/** Unwrap job.result whether flat (API) or nested under .data (AgentOutput). */
export function extractResultPayload(job) {
  const raw = job?.result;
  if (!raw || typeof raw !== "object") return {};

  if (
    raw.data &&
    typeof raw.data === "object" &&
    !Object.prototype.hasOwnProperty.call(raw, "executive_summary")
  ) {
    return raw.data;
  }

  return raw;
}

function formatFilingSource(source) {
  if (!source) return "SEC Filing";
  const match = String(source).match(/([^/]+\.(?:htm|html|txt|pdf))(?:\?|$)/i);
  return match ? match[1] : "SEC Filing";
}

function formatLocation(item, sourceFiling, index) {
  if (item.location) return item.location;
  if (sourceFiling) return formatFilingSource(sourceFiling);
  if (item.filing_value) return "SEC filing match";
  if (item.source === "slide") return "Slide deck";
  if (item.source === "transcript") return "Earnings transcript";
  return index >= 0 ? `Claim ${index + 1}` : "Unknown";
}

function resolveClaimSource(item) {
  const sourceFiling = item.source_filing || item.source_url || "";
  const snippet = item.evidence || item.evidence_snippet || "";

  if (sourceFiling) return formatFilingSource(sourceFiling);
  if (item.source === "slide") return "Slide Deck";
  if (item.source === "transcript") return "Earnings Transcript";
  if (snippet) return "SEC Filing";
  return "Not Found";
}

export function parseVerificationStatus(item) {
  const statusRaw = String(item.status || "").toLowerCase();

  if (
    item.is_consistent === true ||
    statusRaw === "verified" ||
    statusRaw === "consistent"
  ) {
    return "Verified";
  }

  if (
    statusRaw === "unsupported" ||
    statusRaw === "not_found" ||
    (item.is_consistent === false && (item.confidence ?? 0) <= 0.5)
  ) {
    return "Unsupported";
  }

  if (item.is_consistent === false || statusRaw === "flagged") {
    return "Needs Review";
  }

  return "Needs Review";
}

/**
 * Map one filing verification result to a frontend evidence/claim row.
 */
export function parseVerificationItem(item, index) {
  const claim =
    item.claim ||
    item.claim_text ||
    item.text ||
    (item.claimed_value ? String(item.claimed_value) : "");

  const snippet = item.evidence || item.evidence_snippet || "";
  const sourceFiling = item.source_filing || item.source_url || "";

  return {
    id: item.id || `claim-${index}`,
    claim: claim || `Claim ${index + 1}`,
    status: parseVerificationStatus(item),
    confidence:
      clampPercent(item.confidence) ??
      (item.is_consistent ? 85 : item.is_consistent === false ? 25 : 70),
    source: resolveClaimSource(item),
    snippet: snippet || "No supporting filing snippet found.",
    location: formatLocation(item, sourceFiling, index),
    kind: "claim",
  };
}

/**
 * Map a slide KPI to a supplemental evidence row (not a filing-verified claim).
 */
export function parseKpiItem(kpi, index, consistencyScore) {
  const label = kpi.name || kpi.label || `KPI ${index + 1}`;
  const value = String(kpi.value || "").trim();
  const claim = value ? `${label}: ${value}` : label;

  return {
    id: `kpi-${index}`,
    claim,
    status: "Verified",
    confidence: clampPercent(kpi.confidence) ?? consistencyScore ?? 78,
    source: "Slide Deck",
    snippet: kpi.context || `Extracted from slide deck — ${label}.`,
    location: kpi.page ? `Slide ${kpi.page}` : `Slide KPI ${index + 1}`,
    kind: "kpi",
  };
}

export function parseSlideSpeechComparison(item, index, consistencyScore) {
  return {
    id: `comparison-${index}`,
    claim: item.slide_metric || `Comparison ${index + 1}`,
    status: item.status === "reviewed" ? "Verified" : "Needs Review",
    confidence: consistencyScore ?? 78,
    source: "Slide vs Speech",
    snippet: item.speech_reference || "No transcript excerpt available.",
    location: `Comparison ${index + 1}`,
    kind: "comparison",
  };
}

function normalizeClaimKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

/** Avoid duplicating slide KPI rows that already appear in filing verification claims. */
export function appendUniqueKpis(claimRows, kpis, consistencyScore) {
  if (!Array.isArray(kpis) || !kpis.length) return claimRows;

  const seen = new Set(claimRows.map((row) => normalizeClaimKey(row.claim)));

  const extras = [];
  kpis.forEach((kpi, index) => {
    const row = parseKpiItem(kpi, index, consistencyScore);
    const key = normalizeClaimKey(row.claim);
    if (seen.has(key)) return;
    seen.add(key);
    extras.push(row);
  });

  return claimRows.concat(extras);
}

export function parseVerificationResults(rawResults) {
  if (!Array.isArray(rawResults)) return [];
  return rawResults.map((item, index) => parseVerificationItem(item, index));
}

export function parseRiskItem(risk, index) {
  const severityRaw = String(risk.severity || "").toLowerCase();
  let severity = "Medium";
  if (severityRaw === "high" || severityRaw === "critical") severity = "High";
  else if (severityRaw === "low") severity = "Low";

  return {
    count: String(index + 1).padStart(2, "0"),
    label: risk.label || "Detected Risk",
    severity,
    description: risk.description || "Backend analysis flagged this item for review.",
  };
}

/** Map backend job.current_step + status to frontend pipeline card states. */
export function mapJobToProcessingState(job, steps) {
  const backendStatus = job?.status || "pending";
  const backendStep = job?.current_step || "queued";

  if (!steps.length) {
    return { statuses: {}, activeIndex: -1 };
  }

  if (backendStatus === "failed") {
    return {
      statuses: Object.fromEntries(steps.map((step) => [step.id, "Error"])),
      activeIndex: -1,
    };
  }

  if (backendStatus === "completed" || backendStep === "finished") {
    return {
      statuses: Object.fromEntries(steps.map((step) => [step.id, "Complete"])),
      activeIndex: -1,
    };
  }

  const stepOrder = ["ingest", "asr", "vision", "filing", "kpis", "claims", "report"];
  const backendToActiveIndex = {
    queued: 0,
    pending: 0,
    starting: 1,
    analysis: 3,
  };

  const activeIndex = backendToActiveIndex[backendStep] ?? (backendStatus === "running" ? 3 : 0);

  const statuses = Object.fromEntries(
    steps.map((step) => {
      const idx = stepOrder.indexOf(step.id);
      if (idx < 0) return [step.id, "Pending"];
      if (idx < activeIndex) return [step.id, "Complete"];
      if (idx === activeIndex) return [step.id, "Running"];
      return [step.id, "Pending"];
    })
  );

  return { statuses, activeIndex };
}
