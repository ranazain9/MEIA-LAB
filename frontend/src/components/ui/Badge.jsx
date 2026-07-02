function normalizeTone(tone) {
  return String(tone || "neutral").toLowerCase().replace(/\s+/g, "-");
}

export function Badge({ children, className = "", tone = "neutral" }) {
  return <span className={`status-badge ${normalizeTone(tone)} ${className}`.trim()}>{children}</span>;
}

export function StatusBadge({ status }) {
  return <Badge tone={status}>{status}</Badge>;
}
