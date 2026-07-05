import { Navigate, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AccountPage } from "../pages/AccountPage";
import { AuthPage } from "../pages/AuthPage";
import { DrivePage } from "../pages/DrivePage";
import { HomePage } from "../pages/HomePage";
import { RidePage } from "../pages/RidePage";
import { SafetyPage } from "../pages/SafetyPage";
import { AppLayout } from "./AppLayout";
import { useAuth } from "./AuthProvider";
import type { Role } from "../api/types";

function RoleRoute({ allow, children }: { allow: Role[]; children: React.ReactElement }) {
  const { user } = useAuth();
  if (!user || !allow.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export function App() {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="boot-screen">
        <div className="brand-mark large">M</div>
        <span>{t("app.opening")}</span>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={user.role === "driver" ? <DrivePage mode="trip" /> : <HomePage />} />
        <Route path="ride" element={<RoleRoute allow={["rider"]}><RidePage mode="book" /></RoleRoute>} />
        <Route path="ride/activity" element={<RoleRoute allow={["rider"]}><RidePage mode="activity" /></RoleRoute>} />
        <Route path="driver/garage" element={<RoleRoute allow={["driver"]}><DrivePage mode="garage" /></RoleRoute>} />
        <Route path="driver/trips" element={<RoleRoute allow={["driver"]}><DrivePage mode="trips" /></RoleRoute>} />
        <Route path="safety" element={<SafetyPage />} />
        <Route path="account" element={<AccountPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
