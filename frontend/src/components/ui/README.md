# MEIA UI Primitives

Use these components for new hackathon screens so layout, spacing, states, and backend-ready data flow stay consistent.

- `PageHeader` for screen titles and primary actions.
- `SectionHeader` for repeated content groups inside a page.
- `Card` for bordered panels and document surfaces.
- `Button` for button and internal-link actions.
- `Badge` / `StatusBadge` for status text that is not color-only.
- `Tabs` for local filters.
- `DataTable` for dense analyst tables.
- `Skeleton` for service/API loading states.

Recommended screen shape:

```jsx
import { Button, Card, PageHeader, SectionHeader } from "../components/ui";

export function NewScreen() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Workspace"
        title="New Screen"
        subtitle="Backend-ready screen description."
        actions={<Button variant="primary">Run Action</Button>}
      />

      <Card>
        <SectionHeader title="Section" subtitle="Use service-layer data here." />
      </Card>
    </div>
  );
}
```

Keep data fetching in `src/services/*` and pass data into presentational components through props. When the backend is ready, replace service mock returns or normalize backend responses there rather than rewriting screen components.
