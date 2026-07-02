import { Download, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "../layout/ToastProvider.jsx";

export function AnalystBriefPreview({ brief }) {
  const { notify } = useToast();

  return (
    <section className="section-block">
      <p className="section-number">06 / Brief</p>
      <h2>Analyst Brief Preview</h2>
      <div className="brief-preview-card">
        <div>
          <p><strong>{brief.preview.split(".")[0]}.</strong>{brief.preview.substring(brief.preview.indexOf(".") + 1)}</p>
          <div className="button-row">
            <Link className="button primary" to="/brief"><ExternalLink size={16} /> View Full Brief</Link>
            <button className="button secondary" type="button" onClick={() => notify("Demo export completed")}>
              <Download size={16} /> Export Brief
            </button>
          </div>
        </div>
        <dl className="brief-meta">
          <div><dt>Generated</dt><dd>{brief.generated}</dd></div>
          <div><dt>Pages</dt><dd>{brief.pages}</dd></div>
          <div><dt>Citations</dt><dd>{brief.citations}</dd></div>
        </dl>
      </div>
    </section>
  );
}
