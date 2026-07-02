export function Card({ as: Element = "section", children, className = "" }) {
  return <Element className={`ui-card ${className}`.trim()}>{children}</Element>;
}
