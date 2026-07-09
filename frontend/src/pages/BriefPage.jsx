import { Download, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { useToast } from "../components/layout/ToastProvider.jsx";
import { Button } from "../components/ui/Button.jsx";
import { Card } from "../components/ui/Card.jsx";
import { PageHeader } from "../components/ui/PageHeader.jsx";
import { Skeleton } from "../components/ui/Skeleton.jsx";
import { getBrief, getDashboardAnalysis } from "../services/analysisService.js";

export function BriefPage() {
  const [brief, setBrief] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const { notify } = useToast();

  useEffect(() => {
    let mounted = true;
    Promise.all([getBrief(), getDashboardAnalysis()]).then(([briefData, dashboardData]) => {
      if (!mounted) return;
      setBrief(briefData);
      setAnalysis(dashboardData.analysis);
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!brief || !analysis) {
    return <Skeleton className="brief-skeleton" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Analyst Brief"
        title="Analyst Brief"
        subtitle={`Generated evidence-backed summary for ${analysis.company} ${analysis.period}.`}
      />

      <Card className="document-card">
        <div className="document-toolbar">
          <div>
            <p className="section-number">{brief.company} - {brief.period}</p>
            <h2>Evidence-backed Intelligence Brief</h2>
          </div>
          <div className="button-row">
            <Button variant="primary" onClick={() => notify("Demo export completed")}>
              <Download size={16} /> Export Brief
            </Button>
            <Button to="/evidence">
              <ExternalLink size={16} /> Open Evidence Room
            </Button>
          </div>
        </div>

        {brief.sections.map((section) => (
          <article className="brief-section" key={section.title}>
            <h3>{section.title}</h3>
            <p>{section.body}</p>
          </article>
        ))}

        <article className="brief-section">
          <h3>Risks and Watch Items</h3>
          <ul className="brief-risk-list">
            {brief.risks.map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        </article>

        <article className="brief-section">
          <h3>Evidence Citations</h3>
          <div className="citation-grid">
            {brief.citationsList.map((citation) => (
              <span key={citation}>{citation}</span>
            ))}
          </div>
        </article>
      </Card>
    </div>
  );
}
