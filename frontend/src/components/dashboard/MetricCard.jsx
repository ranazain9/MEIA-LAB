export function MetricCard({ metric }) {
  return (
    <article className="metric-tile">
      <div className="metric-top">
        <span>{metric.label}</span>
        <small className={metric.tone === "negative" ? "delta negative" : "delta"}>{metric.delta}</small>
      </div>
      <div className="metric-value">
        {metric.value}
        {metric.suffix ? <span>{metric.suffix}</span> : null}
      </div>
      <strong>{metric.title}</strong>
      <p>{metric.detail}</p>
    </article>
  );
}
