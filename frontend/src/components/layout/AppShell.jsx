import { Outlet } from "react-router-dom";
import { Footer } from "./Footer.jsx";
import { Sidebar } from "./Sidebar.jsx";

export function AppShell() {
  return (
    <div className="app-frame">
      <div className="workspace-frame">
        <Sidebar />
        <main className="main-content">
          <Outlet />
          <Footer />
        </main>
      </div>
    </div>
  );
}
