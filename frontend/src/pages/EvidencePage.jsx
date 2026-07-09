import { useEffect, useMemo, useState } from "react";
import { Card } from "../components/ui/Card.jsx";
import { DataTable } from "../components/ui/DataTable.jsx";
import { PageHeader } from "../components/ui/PageHeader.jsx";
import { Skeleton } from "../components/ui/Skeleton.jsx";
import { StatusBadge } from "../components/ui/Badge.jsx";
import { Tabs } from "../components/ui/Tabs.jsx";
import { getDashboardAnalysis, getEvidenceItems } from "../services/analysisService.js";

const filters = ["All", "Verified", "Needs Review", "Unsupported"];

export function EvidencePage() {
  const [items, setItems] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [active, setActive] = useState("All");

  useEffect(() => {
    let mounted = true;
    Promise.all([getEvidenceItems(), getDashboardAnalysis()]).then(([evidenceData, dashboardData]) => {
      if (!mounted) return;
      setItems(evidenceData);
      setAnalysis(dashboardData.analysis);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(
    () => (active === "All" ? items : items.filter((item) => item.status === active)),
    [active, items]
  );

  const columns = [
    { key: "claim", header: "Claim", render: (item) => <strong>{item.claim}</strong> },
    { key: "status", header: "Status", render: (item) => <StatusBadge status={item.status} /> },
    { key: "confidence", header: "Confidence", render: (item) => <span className="mono-muted">{item.confidence}%</span> },
    { key: "source", header: "Source" },
    { key: "snippet", header: "Evidence snippet" },
    { key: "location", header: "Location", render: (item) => <span className="mono-muted">{item.location}</span> },
  ];

  if (!analysis) {
    return <Skeleton className="table-skeleton" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Evidence Room"
        title="Evidence Room"
        subtitle={`Verified and flagged claims from ${analysis.company} ${analysis.period}.`}
      />

      <Tabs ariaLabel="Evidence status filter" items={filters} onChange={setActive} value={active} />

      <Card className="table-card evidence-table">
        {!items.length ? (
          <Skeleton className="table-skeleton" />
        ) : (
          <DataTable columns={columns} rows={filtered} />
        )}
      </Card>
    </div>
  );
}
