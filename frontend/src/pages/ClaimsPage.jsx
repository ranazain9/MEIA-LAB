import { useEffect, useMemo, useState } from "react";
import { Badge, Card, DataTable, PageHeader, Skeleton, StatusBadge, Tabs } from "../components/ui/index.js";
import { getEvidenceItems } from "../services/analysisService.js";

const filters = ["All", "Verified", "Needs Review", "Unsupported"];

export function ClaimsPage() {
  const [items, setItems] = useState([]);
  const [active, setActive] = useState("All");

  useEffect(() => {
    let mounted = true;
    getEvidenceItems().then((data) => {
      if (mounted) setItems(data);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(
    () => (active === "All" ? items : items.filter((item) => item.status === active)),
    [active, items]
  );

  const counts = useMemo(
    () => ({
      all: items.length,
      verified: items.filter((item) => item.status === "Verified").length,
      review: items.filter((item) => item.status === "Needs Review").length,
      unsupported: items.filter((item) => item.status === "Unsupported").length,
    }),
    [items]
  );

  const columns = [
    { key: "claim", header: "Claim", render: (item) => <strong>{item.claim}</strong> },
    { key: "status", header: "Status", render: (item) => <StatusBadge status={item.status} /> },
    {
      key: "confidence",
      header: "Confidence",
      render: (item) => <span className="mono-muted">{item.confidence}%</span>,
    },
    {
      key: "location",
      header: "Primary Evidence",
      render: (item) => <span className="mono-muted">{item.location}</span>,
    },
  ];

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Verified Claims"
        title="Verified Claims"
        subtitle="Claim-level review queue with verification state, confidence, and primary evidence."
      />

      <div className="claim-summary-grid">
        <ClaimSummary label="Total Claims" value={counts.all} tone="neutral" />
        <ClaimSummary label="Verified" value={counts.verified} tone="Verified" />
        <ClaimSummary label="Needs Review" value={counts.review} tone="Needs Review" />
        <ClaimSummary label="Unsupported" value={counts.unsupported} tone="Unsupported" />
      </div>

      <Tabs ariaLabel="Claim status filter" items={filters} onChange={setActive} value={active} />

      <Card className="table-card claims-table">
        {!items.length ? <Skeleton className="table-skeleton" /> : <DataTable columns={columns} rows={filtered} />}
      </Card>
    </div>
  );
}

function ClaimSummary({ label, tone, value }) {
  return (
    <Card as="article" className="claim-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <Badge tone={tone}>{label}</Badge>
    </Card>
  );
}
