import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell.jsx";
import { ToastProvider } from "./components/layout/ToastProvider.jsx";
import { BriefPage } from "./pages/BriefPage.jsx";
import { ClaimsPage } from "./pages/ClaimsPage.jsx";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { EvidencePage } from "./pages/EvidencePage.jsx";
import { ProcessingPage } from "./pages/ProcessingPage.jsx";

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/claims" element={<ClaimsPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/brief" element={<BriefPage />} />
          <Route path="/processing" element={<ProcessingPage />} />
          <Route path="*" element={<Navigate replace to="/dashboard" />} />
        </Route>
      </Routes>
    </ToastProvider>
  );
}
