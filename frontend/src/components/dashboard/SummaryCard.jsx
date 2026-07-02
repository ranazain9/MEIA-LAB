import { Check, Activity } from "lucide-react";

export function SummaryCard({ analysis }) {
  return (
    <section className="summary-card">
      <div>
        <p className="section-kicker"><Activity size={15} /> Analysis Summary</p>
        <span className="small-label">Overall Signal</span>
        <h2>{analysis.headline}</h2>
        <p>{analysis.summary}</p>
      </div>
      <div className="summary-checklist">
        {analysis.checklist.map((item) => (
          <span key={item}>
            <Check size={16} /> {item}
          </span>
        ))}
      </div>
    </section>
  );
}
