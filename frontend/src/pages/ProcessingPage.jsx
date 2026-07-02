import { Check, Clock, Play, TriangleAlert, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useToast } from "../components/layout/ToastProvider.jsx";
import { Badge } from "../components/ui/Badge.jsx";
import { Button } from "../components/ui/Button.jsx";
import { Card } from "../components/ui/Card.jsx";
import { PageHeader } from "../components/ui/PageHeader.jsx";
import {
  applyBackendJob,
  getProcessingSteps,
  pollJob,
  startAnalysis,
} from "../services/analysisService.js";

const initialStatus = "Pending";

export function ProcessingPage() {
  const [steps, setSteps] = useState([]);
  const [statuses, setStatuses] = useState({});
  const [running, setRunning] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [ticker, setTicker] = useState("AMD");
  const [audio, setAudio] = useState(null);
  const [slides, setSlides] = useState(null);
  const [job, setJob] = useState(null);
  const [jobLoading, setJobLoading] = useState(false);
  const { notify } = useToast();

  useEffect(() => {
    let mounted = true;
    getProcessingSteps().then((data) => {
      if (!mounted) return;
      setSteps(data);
      setStatuses(Object.fromEntries(data.map((step) => [step.id, initialStatus])));
    });
    return () => {
      mounted = false;
    };
  }, []);

  const progress = useMemo(() => {
    if (!steps.length) return 0;
    const completed = steps.filter((step) => ["Complete", "Warning", "Error"].includes(statuses[step.id])).length;
    return Math.round((completed / steps.length) * 100);
  }, [steps, statuses]);

  function runDemoAnalysis() {
    if (running || !steps.length) return;
    setRunning(true);
    setActiveIndex(0);
    setStatuses(Object.fromEntries(steps.map((step) => [step.id, initialStatus])));

    steps.forEach((step, index) => {
      window.setTimeout(() => {
        setActiveIndex(index);
        setStatuses((current) => ({ ...current, [step.id]: "Running" }));
      }, index * 700);

      window.setTimeout(() => {
        const finalStatus = step.id === "kpis" ? "Warning" : step.id === "claims" ? "Error" : "Complete";
        setStatuses((current) => ({ ...current, [step.id]: finalStatus }));
        if (index === steps.length - 1) {
          setRunning(false);
          setActiveIndex(-1);
          notify("Demo analysis completed");
        }
      }, index * 700 + 520);
    });
  }

  async function handleBackendSubmit(event) {
    event.preventDefault();
    if (!ticker || !audio || !slides || jobLoading) return;
    setJobLoading(true);
    setJob(null);
    try {
      const started = await startAnalysis({ ticker, audio, slides });
      const finished = await pollJob(started.job_id, {
        intervalMs: 2000,
        onUpdate: setJob,
      });
      setJob(finished);
      if (finished.status === "completed") {
        applyBackendJob(finished);
        notify("Backend analysis mapped into dashboard");
      } else {
        notify(finished.error || "Backend analysis failed");
      }
    } catch (error) {
      notify(error.message || "Backend analysis failed");
    } finally {
      setJobLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <Button disabled={running || !steps.length} onClick={runDemoAnalysis} variant="primary">
            <Play size={16} /> {running ? "Running Demo" : "Run Demo Analysis"}
          </Button>
        }
        eyebrow="Processing"
        split
        title="Processing Pipeline"
        subtitle="Simulated multi-agent ingestion and verification workflow."
      />

      <Card className="pipeline-shell">
        <div className="pipeline-head">
          <p className="small-label">MEIA Workspace · AMD Q2 2026</p>
          <span>{running ? `Step ${activeIndex + 1} running` : `${progress}% complete`}</span>
        </div>
        <div className="progress-track">
          <span style={{ width: `${progress}%` }} />
        </div>
        <div className="pipeline-grid">
          {steps.map((step, index) => (
            <StepCard
              active={activeIndex === index}
              key={step.id}
              status={statuses[step.id] || initialStatus}
              step={step}
            />
          ))}
        </div>
      </Card>

      <Card className="backend-run-card">
        <div>
          <p className="section-number">Backend Integration</p>
          <h2>Run Real API Analysis</h2>
          <p>Upload earnings assets to the existing FastAPI job endpoint. Completed results hydrate dashboard fields where the backend provides data.</p>
        </div>
        <form className="backend-form" onSubmit={handleBackendSubmit}>
          <label>
            Ticker
            <input maxLength={10} onChange={(event) => setTicker(event.target.value.toUpperCase())} value={ticker} />
          </label>
          <label>
            Earnings Call Audio
            <span className="file-input-shell">
              <input accept="audio/*,.wav,.mp3,.m4a" onChange={(event) => setAudio(event.target.files?.[0] || null)} type="file" />
              <span>{audio?.name || "Choose audio file"}</span>
            </span>
          </label>
          <label>
            Slide Deck
            <span className="file-input-shell">
              <input accept="application/pdf,.pdf" onChange={(event) => setSlides(event.target.files?.[0] || null)} type="file" />
              <span>{slides?.name || "Choose slide deck"}</span>
            </span>
          </label>
          <Button className="full-width" disabled={!ticker || !audio || !slides || jobLoading} type="submit">
            <Upload size={16} /> {jobLoading ? "Polling Backend" : "Start Backend Analysis"}
          </Button>
        </form>
        {job ? (
          <p className="job-line">
            Job {job.job_id?.slice(0, 8)} · {job.status}
            {job.ticker ? ` · ${job.ticker}` : ""}
          </p>
        ) : null}
      </Card>
    </div>
  );
}

function StepCard({ active, status, step }) {
  const Icon = status === "Complete" ? Check : status === "Warning" || status === "Error" ? TriangleAlert : Clock;
  return (
    <article className={`step-card ${active ? "active" : ""}`}>
      <div className="step-icon"><Icon size={18} /></div>
      <div>
        <Badge tone={status}>{status}</Badge>
        <h3>{step.title}</h3>
        <p>{step.description}</p>
        <small>{step.duration}</small>
      </div>
    </article>
  );
}
