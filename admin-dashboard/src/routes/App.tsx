import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { MatchesPage } from "../pages/MatchesPage";
import { PaymentsPage } from "../pages/PaymentsPage";
import { ReportsPage } from "../pages/ReportsPage";
import { RideRequestsPage } from "../pages/RideRequestsPage";
import { SOSEventsPage } from "../pages/SOSEventsPage";
import { TripsPage } from "../pages/TripsPage";
import { UsersPage } from "../pages/UsersPage";
import { VehiclesPage } from "../pages/VehiclesPage";
import { AuditLogsPage } from "../pages/AuditLogsPage";
import { useAuth } from "./AuthProvider";
import { AppLayout } from "./AppLayout";

function ProtectedRoutes() {
  const { user, loading } = useAuth();
  if (loading) return <div className="boot-screen" />;
  if (!user) return <Navigate to="/login" replace />;
  return <AppLayout />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoutes />}>
        <Route index element={<DashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="vehicles" element={<VehiclesPage />} />
        <Route path="ride-requests" element={<RideRequestsPage />} />
        <Route path="trips" element={<TripsPage />} />
        <Route path="matches" element={<MatchesPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="sos" element={<SOSEventsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="audit" element={<AuditLogsPage />} />
      </Route>
    </Routes>
  );
}
