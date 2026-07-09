import {
  BarChart3,
  BookOpen,
  CheckSquare,
  Cpu,
  FileText,
  LayoutDashboard,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/dashboard", match: ["/", "/dashboard"], icon: LayoutDashboard },
  { label: "Verified Claims", to: "/claims", match: ["/claims"], icon: CheckSquare },
  { label: "Evidence Room", to: "/evidence", icon: BookOpen },
  { label: "Analyst Brief", to: "/brief", icon: FileText },
  { label: "Processing", to: "/processing", icon: Cpu },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <div>
        <div className="brand-block">
          <div className="brand-row">
            <strong>MEIA</strong>
            <span>Multimodal Earnings Intelligence</span>
          </div>
        </div>
        <nav className="side-nav" aria-label="Workspace">
          <p className="rail-label">Workspace</p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const matches = item.match || [item.to];
            const isActive = matches.includes(location.pathname);
            return (
              <Link
                className={`side-link ${isActive ? "active" : ""}`}
                key={`${item.label}-${item.to}`}
                to={item.to}
              >
                <Icon size={17} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="workspace-card">
        <BarChart3 size={18} />
        <div>
          <strong>MEIA v1</strong>
          <span>AMD - MI300X</span>
        </div>
      </div>
    </aside>
  );
}
