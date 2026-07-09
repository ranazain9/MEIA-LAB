import { Download, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "../layout/ToastProvider.jsx";

export function AnalysisHeader({ analysis }) {
  const { notify } = useToast();

  return (
    <section className="analysis-header">
      <div className="analysis-title-row">
        <div className="brand-inline">
          <strong>MEIA</strong>
          <span>Multimodal Earnings Intelligence</span>
        </div>
        <div className="analysis-meta">
          <span>Analysis</span>
          <strong>
            {analysis.company} - {analysis.period}
          </strong>
          <span>{analysis.status}</span>
          {analysis.generated ? <span>{analysis.generated}</span> : null}
        </div>
      </div>
      <div className="analysis-actions">
        <span className="verified-pill">
          <span />
          Verified Analysis
        </span>
        <Link className="button secondary" to="/evidence">
          <ExternalLink size={16} /> Open Evidence
        </Link>
        <button className="button primary" type="button" onClick={() => notify("Demo export completed")}>
          <Download size={16} /> Export Brief
        </button>
      </div>
    </section>
  );
}
