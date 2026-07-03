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
        <Route index element={<HomePage />} />
        <Route path="ride" element={<RidePage />} />
        <Route path="drive" element={<DrivePage />} />
        <Route path="safety" element={<SafetyPage />} />
        <Route path="account" element={<AccountPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
