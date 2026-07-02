export function RiskMonitor({ risks }) {
  return (
    <section className="section-block">
      <p className="small-label">Risk</p>
      <h2>Risk Monitor</h2>
      <p className="section-description">
        Findings flagged across financial, guidance, communication, and verification dimensions.
      </p>
      <div className="risk-list-panel">
        {risks.map((risk) => (
          <article key={`${risk.label}-${risk.count}`} className="risk-row">
            <strong className="risk-count">{risk.count}</strong>
            <h3>{risk.label}</h3>
            <span className={`severity-badge ${risk.severity.toLowerCase()}`}>{risk.severity}</span>
            <p>{risk.description}</p>
            <button className="row-action" type="button">View ↗</button>
          </article>
        ))}
      </div>
      <p className="fine-print">Communication signals are supporting indicators, not verified financial facts.</p>
    </section>
  );
}
