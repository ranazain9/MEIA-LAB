export function PageHeader({ actions, eyebrow, split = false, subtitle, title }) {
  return (
    <section className={`page-title ${split ? "split" : ""}`.trim()}>
      <div>
        {eyebrow ? <p className="section-number">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </section>
  );
}

export function SectionHeader({ action, eyebrow, subtitle, title }) {
  return (
    <div className={action ? "section-heading-row" : ""}>
      <div>
        {eyebrow ? <p className="section-number">{eyebrow}</p> : null}
        <h2>{title}</h2>
        {subtitle ? <p className="section-description">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
