export function DataQualityCard({ quality }) {
  return (
    <section className="quality-card">
      <div className="quality-head">
        <div>
          <h2>Most Recent Data Quality</h2>
          <p>Snapshot of the current analysis ingestion.</p>
        </div>
        <button className="link-button" type="button">Export Source Data -&gt;</button>
      </div>
      <div className="quality-body">
        <div className="quality-score-block">
          <div className="score-ring" aria-label={`Score ${quality.score} out of 100`}>
            <span>Score</span>
            <strong>{quality.score}</strong>
            <small>/ 100</small>
          </div>
          <div>
            <p className="small-label">Transcript Score</p>
            <h3>{quality.transcriptScore}</h3>
            <span className="soft-badge">{quality.transcriptBadge}</span>
          </div>
          <dl className="compact-list">
            {quality.metrics.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="stat-table">
          <p className="small-label">Recent Data Stats</p>
          {quality.stats.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
