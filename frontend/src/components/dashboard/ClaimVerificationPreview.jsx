import { Link } from "react-router-dom";

export function ClaimVerificationPreview({ items }) {
  return (
    <section className="section-block">
      <div className="section-heading-row">
        <div>
          <p className="small-label">Verification</p>
          <h2>Claim Verification</h2>
          <p className="section-description">Management statements cross-checked against slides and filings.</p>
        </div>
        <Link className="link-button" to="/evidence">View all {items.length} claims ↗</Link>
      </div>
      <div className="table-card compact">
        <table>
          <thead>
            <tr>
              <th>Claim</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Evidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 3).map((item) => (
              <tr key={item.id}>
                <td><strong>"{item.claim}"</strong></td>
                <td><span className={`status-dot ${item.status.toLowerCase().replace(" ", "-")}`} />{item.status}</td>
                <td>{item.confidence >= 80 ? "High" : item.confidence >= 60 ? "Medium" : "Low"}</td>
                <td className="mono-muted">{item.source || item.location}</td>
                <td><Link className="row-action" to="/evidence">Review ↗</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
