import { useState } from "react";

const tabs = ["Consistency", "Risk Flags", "Verified Claims"];

export function TrendPanel({ analysis }) {
  const [active, setActive] = useState("Consistency");
  const points = analysis.chart;
  const key =
    active === "Risk Flags" ? "riskFlags" : active === "Verified Claims" ? "verifiedClaims" : "consistency";
  const values = points.map((point) => point[key]);
  const max = Math.max(...values, 100);
  const polyline = points
    .map((point, index) => {
      const x = 28 + index * 45;
      const y = 112 - (point[key] / max) * 82;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <section className="section-block">
      <p className="section-number">02 / Trends</p>
      <h2>Historical Analytics</h2>
      <p className="section-description">
        Quarter-over-quarter movement across verification, risk, and communication signals.
      </p>
      <div className="trend-panel">
        <div className="trend-stat-grid">
          {analysis.trendSummary.map((item) => (
            <div key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <small>{item.previous}</small>
              <em>{item.delta}</em>
            </div>
          ))}
        </div>
        <div className="tabs" role="tablist" aria-label="Historical analytics metric">
          {tabs.map((tab) => (
            <button
              aria-selected={active === tab}
              className={active === tab ? "active" : ""}
              key={tab}
              onClick={() => setActive(tab)}
              role="tab"
              type="button"
            >
              {tab}
            </button>
          ))}
        </div>
        <svg className="trend-chart" viewBox="0 0 120 120" preserveAspectRatio="none" role="img" aria-label={`${active} trend chart`}>
          <line x1="20" x2="114" y1="112" y2="112" />
          <line x1="20" x2="20" y1="12" y2="112" />
          <polyline points={polyline} />
          {points.map((point, index) => {
            const x = 28 + index * 45;
            const y = 112 - (point[key] / max) * 82;
            return <circle cx={x} cy={y} key={point.label} r="0.65" />;
          })}
        </svg>
        <div className="chart-labels">
          {points.map((point) => (
            <span key={point.label}>{point.label}</span>
          ))}
        </div>
      </div>
    </section>
  );
}
