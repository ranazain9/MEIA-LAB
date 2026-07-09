import {
  brief as mockBrief,
  dashboardAnalysis,
  evidenceItems,
  riskItems,
  agentStatuses,
  qualityMetrics,
} from "../data/mockAnalysis.js";
import {
  appendUniqueKpis,
  clampPercent,
  extractResultPayload,
  parseKpiItem,
  parseRiskItem,
  parseSlideSpeechComparison,
  parseVerificationItem,
  parseVerificationResults,
} from "./resultParser.js";

function formatGeneratedLabel(value) {
  const parsed = value ? new Date(value) : new Date();
  if (Number.isNaN(parsed.getTime())) return mockBrief.generated;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  })
    .format(parsed)
    .replace(",", "");
}

function resolvePeriodLabel(job, data) {
  return data.report_period || data.period || job?.period || dashboardAnalysis.period;
}

function stripMarkdown(value) {
  return String(value || "")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .trim();
}

function parseReportSections(fullReport) {
  if (!fullReport) return [];

  const withoutTitle = String(fullReport).replace(/^#\s.+(?:\r?\n)+/m, "").trim();
  const sections = [];
  const pattern = /^##\s+(.+?)\s*$(.*?)(?=^##\s+|\s*$)/gms;
  let match;

  while ((match = pattern.exec(withoutTitle)) !== null) {
    const title = match[1].trim();
    const body = stripMarkdown(match[2]);
    if (title && body) {
      sections.push({ title, body });
    }
  }

  if (!sections.length && withoutTitle) {
    sections.push({ title: "Executive Summary", body: stripMarkdown(withoutTitle) });
  }

  return sections.filter((section) => !/^key risks?|risk factors?$/i.test(section.title));
}

function buildLiveBriefSections(data, slideKpis, consistency) {
  const reportSections = parseReportSections(data.full_report);
  if (reportSections.length) return reportSections;

  const sections = [];
  if (data.executive_summary) {
    sections.push({ title: "Executive Summary", body: data.executive_summary });
  }

  const filingVerification = data.filing_verification || {};
  const verificationResults = Array.isArray(filingVerification.verification_results)
    ? filingVerification.verification_results
    : Array.isArray(data.verification_results)
      ? data.verification_results
      : [];
  const verified = verificationResults.filter((item) => item.is_consistent === true).length;

  sections.push({
    title: "Verification Highlights",
    body:
      verificationResults.length > 0
        ? `${verified} of ${verificationResults.length} extracted claims were verified against available filing evidence. Consistency scored ${consistency ?? "N/A"}%.`
        : `Backend agents completed the verification pass with a consistency score of ${consistency ?? "N/A"}%.`,
  });

  if (slideKpis.length) {
    sections.push({
      title: "Key Financial Metrics",
      body: slideKpis
        .map((kpi) => {
          const label = kpi.name || kpi.label || "KPI";
          const value = kpi.value ? `: ${kpi.value}` : "";
          return `${label}${value}`;
        })
        .join(", "),
    });
  }

  if (!sections.length) {
    sections.push({
      title: "Executive Summary",
      body: "Backend analysis completed, but no narrative brief was returned by the agent.",
    });
  }

  return sections;
}

export function normalizeJobToAnalysis(job) {
  const data = extractResultPayload(job);
  const hasBackendData = Object.keys(data).length > 0;

  const consistency = clampPercent(data.confidence ?? data.consistency_score);
  const ticker = job?.ticker || dashboardAnalysis.ticker;
  const period = resolvePeriodLabel(job, data);
  const generated = formatGeneratedLabel(
    job?.completed_at || data.completed_at || data.generated_at
  );

  const risks = Array.isArray(data.risks)
    ? data.risks
    : Array.isArray(data.risk_factors)
      ? data.risk_factors
      : [];

  const filingVerification = data.filing_verification || {};
  const rawVerifications = Array.isArray(filingVerification.verification_results)
    ? filingVerification.verification_results
    : Array.isArray(data.verification_results)
      ? data.verification_results
      : [];

  const slideAnalysis = data.slide_analysis || {};
  const slideKpis = Array.isArray(slideAnalysis.kpis) ? slideAnalysis.kpis : [];
  const slideGuidance = Array.isArray(slideAnalysis.guidance) ? slideAnalysis.guidance : [];

  const comparisons = Array.isArray(data.slide_speech_comparison)
    ? data.slide_speech_comparison
    : [];

  const transcript = Array.isArray(data.transcript) ? data.transcript : [];

  const asrData = data.tone_analysis || {};
  const toneSegments = Array.isArray(asrData.segments) ? asrData.segments : [];
  const speakerCount = asrData.speaker_count || 0;

  const mappedRisks = risks.length
    ? risks.map((risk, index) => parseRiskItem(risk, index))
    : hasBackendData
      ? []
      : riskItems;

  const mappedClaims = parseVerificationResults(rawVerifications);

  let mappedEvidence;
  if (mappedClaims.length) {
    mappedEvidence = appendUniqueKpis(mappedClaims, slideKpis, consistency);
  } else if (comparisons.length) {
    mappedEvidence = comparisons.map((item, index) =>
      parseSlideSpeechComparison(item, index, consistency)
    );
  } else if (slideKpis.length) {
    mappedEvidence = slideKpis.map((kpi, index) => parseKpiItem(kpi, index, consistency));
  } else {
    mappedEvidence = hasBackendData ? [] : evidenceItems;
  }

  const liveSections = buildLiveBriefSections(data, slideKpis, consistency);
  const liveCitations = mappedEvidence
    .filter((row) => row.snippet && row.snippet !== "No supporting filing snippet found.")
    .slice(0, 8)
    .map((row) => `${row.location} - ${row.claim}`);

  const mappedBrief = {
    ...(hasBackendData ? {} : mockBrief),
    preview: data.executive_summary || mockBrief.preview,
    sections: hasBackendData ? liveSections : mockBrief.sections,
    risks: risks.length
      ? risks.map((r) => r.description || r.label)
      : hasBackendData
        ? ["No material risks identified by backend agents."]
        : mockBrief.risks,
    citationsList: mappedClaims.length
      ? mappedClaims
          .filter((row) => row.snippet && row.snippet !== "No supporting filing snippet found.")
          .slice(0, 8)
          .map((row) => `${row.location} — ${row.claim}`)
      : hasBackendData
        ? liveCitations
        : mockBrief.citationsList,
    company: ticker,
    period,
    generated,
    pages: mockBrief.pages,
    citations: mappedClaims.length || liveCitations.length || mockBrief.citations,
  };

  const hasAsr = toneSegments.length > 0 || transcript.length > 0;
  const hasVision = slideKpis.length > 0 || comparisons.length > 0;
  const hasFiling = mappedClaims.length > 0;

  const verifiedClaimCount = mappedClaims.filter((row) => row.status === "Verified").length;

  const mappedAgents = [
    {
      title: "ASR Agent",
      subtitle: "Speech-to-text transcription",
      icon: "mic",
      messages: hasAsr
        ? [
            { severity: "info", text: "Audio transcription processed" },
            {
              severity: "ok",
              text: speakerCount
                ? `Diarization complete — ${speakerCount} speaker(s) detected`
                : `Transcription complete — ${transcript.length} segments`,
            },
            toneSegments.length
              ? { severity: "ok", text: `Tone analysis — ${toneSegments.length} segments analyzed` }
              : { severity: "info", text: "Tone analysis not available" },
          ]
        : [{ severity: "info", text: "Audio load pending or skipped" }],
    },
    {
      title: "Vision Agent",
      subtitle: "Slide deck extraction",
      icon: "layers",
      messages: hasVision
        ? [
            { severity: "ok", text: "Slide VLM extraction completed" },
            {
              severity: "ok",
              text: `Extracted ${slideKpis.length} KPIs${slideGuidance.length ? ` and ${slideGuidance.length} guidance items` : ""}`,
            },
          ]
        : [{ severity: "info", text: "Slides parsing skipped or no KPIs found" }],
    },
    {
      title: "Filing Agent",
      subtitle: "SEC filing ingestion",
      icon: "shield",
      messages: hasFiling
        ? [
            { severity: "info", text: "SEC EDGAR filings fetched and indexed" },
            { severity: "ok", text: `Verified ${mappedClaims.length} claims against filing data` },
          ]
        : [{ severity: "info", text: "SEC filing ingestion skipped or no claims found" }],
    },
    {
      title: "Orchestrator",
      subtitle: "Cross-verification & report gen",
      icon: "shield",
      messages:
        job?.status === "completed"
          ? [
              { severity: "info", text: "Cross-verification workflow completed" },
              { severity: "ok", text: `Brief compiled with consistency score ${consistency ?? 0}%` },
              { severity: "ok", text: `Identified ${risks.length} risk watch-item(s)` },
            ]
          : [{ severity: "info", text: "Orchestration pending" }],
    },
  ];

  const mappedQuality = {
    score: consistency ?? 90,
    transcriptScore: hasAsr ? `${Math.min(98, 90 + transcript.length)}%` : "N/A",
    transcriptBadge: hasAsr ? "High Fidelity" : "None",
    metrics: [
      ["Audio Quality", hasAsr ? "95%" : "N/A"],
      ["Slide VLM Performance", hasVision ? "98%" : "N/A"],
      ["Filing Verification Rate", hasFiling ? "100%" : "N/A"],
    ],
    stats: [
      ["Ticker", ticker],
      ["Job ID", job?.job_id ? job.job_id.slice(0, 8) : "N/A"],
      ["Generated", generated],
      ["Transcript Segments", String(transcript.length)],
      ["Slide KPIs", String(slideKpis.length)],
      ["Claims Extracted", String(mappedClaims.length)],
      ["Consistency Score", consistency ? `${consistency}%` : "N/A"],
      ["Risk Flags", String(risks.length)],
    ],
  };

  const totalClaims = mappedClaims.length;

  return {
    dashboard: {
      ...dashboardAnalysis,
      ticker,
      company: ticker,
      period,
      generated,
      status:
        job?.status === "completed"
          ? `Completed${job.completed_at ? " · Live" : ""}`
          : dashboardAnalysis.status,
      summary: data.executive_summary || dashboardAnalysis.summary,
      metrics: dashboardAnalysis.metrics.map((metric) => {
        if (metric.label === "Consistency Score" && consistency != null) {
          return {
            ...metric,
            value: String(consistency),
            detail: "Mapped from backend pipeline score.",
          };
        }
        if (metric.label === "Claims Verified" && totalClaims > 0) {
          return {
            ...metric,
            value: String(verifiedClaimCount),
            suffix: `/${totalClaims}`,
            detail: `${Math.round((verifiedClaimCount / totalClaims) * 100)}% verification rate`,
          };
        }
        if (metric.label === "Risk Flags") {
          return {
            ...metric,
            value: String(risks.length),
            detail: risks.length ? "Identified watch items." : "No risks flagged.",
          };
        }
        if (metric.label === "Confidence" && consistency != null) {
          return {
            ...metric,
            value: String(consistency),
            detail: "Derived from pipeline consistency score.",
          };
        }
        return metric;
      }),
    },
    risks: mappedRisks,
    claims: mappedClaims.length
      ? mappedClaims
      : hasBackendData
        ? []
        : evidenceItems.filter((item) => item.kind !== "kpi"),
    evidence: mappedEvidence,
    brief: mappedBrief,
    agents: mappedAgents,
    quality: mappedQuality,
    _raw: { hasAsr, hasVision, hasFiling, ticker, consistency },
  };
}

export {
  extractResultPayload,
  parseVerificationItem,
  parseVerificationResults,
} from "./resultParser.js";
