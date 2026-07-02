import { useMemo, useState } from "react";
import { pollJob, startAnalysis } from "./api.js";

const STEPS = [
  { key: "pending", label: "Queued" },
  { key: "running", label: "Agents running" },
  { key: "completed", label: "Report ready" },
];

function StatusTimeline({ status }) {
  const activeIndex =
    status === "failed"
      ? 1
      : status === "completed"
        ? 2
        : status === "running"
          ? 1
          : 0;

  return (
    <div className="timeline">
      {STEPS.map((step, index) => (
        <div
          key={step.key}
          className={`timeline-step ${index <= activeIndex ? "active" : ""} ${
            status === "failed" && index === 1 ? "failed" : ""
          }`}
        >
          <div className="dot" />
          <span>{step.label}</span>
        </div>
      ))}
    </div>
  );
}

function MetricCard({ label, value, tone = "default" }) {
  return (
    <div className={`metric-card tone-${tone}`}>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
    </div>
  );
}

function ReportPanel({ result }) {
  const data = result?.data || {};
  const risks = data.risk_factors || [];

  return (
    <section className="report-grid">
      <article className="panel span-2">
        <h2>Executive Summary</h2>
        <p>{data.executive_summary || "No summary generated."}</p>
      </article>

      <MetricCard
        label="Consistency Score"
        value={
          typeof data.consistency_score === "number"
            ? data.consistency_score.toFixed(2)
            : "—"
        }
        tone={
          (data.consistency_score || 0) >= 0.8
            ? "good"
            : (data.consistency_score || 0) >= 0.5
              ? "warn"
              : "bad"
        }
      />

      <MetricCard
        label="Speakers Detected"
        value={data.tone_analysis?.speaker_count ?? "—"}
      />

      <article className="panel">
        <h2>Risk Factors</h2>
        {risks.length === 0 ? (
          <p className="muted">No risks flagged.</p>
        ) : (
          <ul className="risk-list">
            {risks.map((risk, index) => (
              <li key={`${risk.label}-${index}`}>
                <span className={`severity ${risk.severity}`}>{risk.severity}</span>
                <div>
                  <strong>{risk.label}</strong>
                  <p>{risk.description}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </article>

      <article className="panel">
        <h2>Slide vs Speech</h2>
        {(data.slide_speech_comparison || []).length === 0 ? (
          <p className="muted">No comparisons available.</p>
        ) : (
          <ul className="comparison-list">
            {data.slide_speech_comparison.map((item, index) => (
              <li key={index}>
                <strong>{item.slide_metric}</strong>
                <p>{item.speech_reference}</p>
              </li>
            ))}
          </ul>
        )}
      </article>

      <article className="panel span-2">
        <h2>Full Report</h2>
        <pre className="report-markdown">{data.full_report || "No report body."}</pre>
      </article>
    </section>
  );
}

export default function App() {
  const [ticker, setTicker] = useState("AMD");
  const [audio, setAudio] = useState(null);
  const [slides, setSlides] = useState(null);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = useMemo(
    () => Boolean(ticker.trim() && audio && slides && !loading),
    [ticker, audio, slides, loading]
  );

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    setJob(null);

    try {
      const started = await startAnalysis({ ticker: ticker.trim(), audio, slides });
      const finished = await pollJob(started.job_id, {
        onUpdate: setJob,
      });
      setJob(finished);
      if (finished.status === "failed") {
        setError(finished.error || "Analysis failed.");
      }
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Multimodal Earnings Intelligence Agent</p>
          <h1>MEIA Dashboard</h1>
          <p className="subtitle">
            Upload an earnings call and slide deck. MEIA runs ASR, vision, SEC
            filing verification, and synthesizes an analyst brief.
          </p>
        </div>
        <div className="hero-badge">AMD Hackathon 2026</div>
      </header>

      <main className="layout">
        <section className="panel upload-panel">
          <h2>Run Analysis</h2>
          <form className="upload-form" onSubmit={handleSubmit}>
            <label>
              Ticker
              <input
                value={ticker}
                onChange={(event) => setTicker(event.target.value.toUpperCase())}
                placeholder="AMD"
                maxLength={10}
              />
            </label>

            <label>
              Earnings Call Audio
              <input
                type="file"
                accept="audio/*,.wav,.mp3,.m4a"
                onChange={(event) => setAudio(event.target.files?.[0] || null)}
              />
            </label>

            <label>
              Slide Deck (PDF)
              <input
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => setSlides(event.target.files?.[0] || null)}
              />
            </label>

            <button type="submit" disabled={!canSubmit}>
              {loading ? "Analyzing…" : "Start Analysis"}
            </button>
          </form>

          {error ? <p className="error">{error}</p> : null}

          {job ? (
            <div className="job-status">
              <StatusTimeline status={job.status} />
              <p className="muted">
                Job {job.job_id?.slice(0, 8)} · {job.status}
                {job.ticker ? ` · ${job.ticker}` : ""}
              </p>
            </div>
          ) : null}
        </section>

        {job?.status === "completed" && job.result ? (
          <ReportPanel result={job.result} />
        ) : (
          <section className="panel empty-state">
            <h2>Analyst Intelligence Brief</h2>
            <p className="muted">
              Results will appear here after the orchestrator finishes ASR, vision,
              SEC cross-check, and report synthesis.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
