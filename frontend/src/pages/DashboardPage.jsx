import { useEffect, useState } from "react";
import { AgentStatusCard } from "../components/dashboard/AgentStatusCard.jsx";
import { AnalystBriefPreview } from "../components/dashboard/AnalystBriefPreview.jsx";
import { AnalysisHeader } from "../components/dashboard/AnalysisHeader.jsx";
import { ClaimVerificationPreview } from "../components/dashboard/ClaimVerificationPreview.jsx";
import { DataQualityCard } from "../components/dashboard/DataQualityCard.jsx";
import { MetricCard } from "../components/dashboard/MetricCard.jsx";
import { RiskMonitor } from "../components/dashboard/RiskMonitor.jsx";
import { SummaryCard } from "../components/dashboard/SummaryCard.jsx";
import { TrendPanel } from "../components/dashboard/TrendPanel.jsx";
import { getBrief, getDashboardAnalysis, getEvidenceItems } from "../services/analysisService.js";

export function DashboardPage() {
  const [data, setData] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [brief, setBrief] = useState(null);

  useEffect(() => {
    let mounted = true;
    Promise.all([getDashboardAnalysis(), getEvidenceItems(), getBrief()]).then(([dashboard, items, briefData]) => {
      if (!mounted) return;
      setData(dashboard);
      setEvidence(items);
      setBrief(briefData);
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!data || !brief) {
    return <DashboardSkeleton />;
  }

  return (
    <>
      <AnalysisHeader analysis={data.analysis} />
      <div className="dashboard-page">
        <section className="hero-copy">
          <p className="small-label">Dashboard</p>
          <h1>Earnings Intelligence</h1>
          <p>AI-verified analysis of audio, slides, and official filings for AMD Q2 2026 earnings.</p>
        </section>

        <SummaryCard analysis={data.analysis} />

        <section className="section-block">
          <p className="small-label">Performance</p>
          <h2>Performance Overview</h2>
          <p className="section-description">Core verification, risk, and confidence indicators for this earnings call.</p>
          <div className="metric-grid">
            {data.analysis.metrics.map((metric) => (
              <MetricCard key={metric.label} metric={metric} />
            ))}
          </div>
        </section>

        <TrendPanel analysis={data.analysis} />
        <ClaimVerificationPreview items={evidence} />
        <RiskMonitor risks={data.risks} />

        <section className="section-block">
          <p className="small-label">Pipeline</p>
          <h2>Agent & Source Status</h2>
          <p className="section-description">Parallel agent execution and latest source quality from the current earnings analysis.</p>
          <div className="agent-grid">
            {data.agents.map((agent) => (
              <AgentStatusCard agent={agent} key={agent.title} />
            ))}
          </div>
        </section>

        <DataQualityCard quality={data.quality} />
        <AnalystBriefPreview brief={brief} />
      </div>
    </>
  );
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-page">
      <div className="skeleton hero-skeleton" />
      <div className="skeleton summary-skeleton" />
      <div className="skeleton-grid">
        {Array.from({ length: 5 }).map((_, index) => (
          <div className="skeleton metric-skeleton" key={index} />
        ))}
      </div>
    </div>
  );
}
