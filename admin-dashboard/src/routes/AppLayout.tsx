import { Button } from "@movu/ui";
import {
  AlertTriangle,
  Car,
  CreditCard,
  Gauge,
  GitMerge,
  LogOut,
  MessageSquareWarning,
  Route,
  ShieldCheck,
  ScrollText,
  Users
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { useAuth } from "./AuthProvider";

const navItems = [
  { to: "/", key: "dashboard", icon: Gauge },
  { to: "/users", key: "users", icon: Users },
  { to: "/vehicles", key: "vehicles", icon: Car },
  { to: "/ride-requests", key: "rideRequests", icon: Route },
  { to: "/trips", key: "trips", icon: ShieldCheck },
  { to: "/matches", key: "matches", icon: GitMerge },
  { to: "/payments", key: "payments", icon: CreditCard },
  { to: "/sos", key: "sos", icon: AlertTriangle },
  { to: "/reports", key: "reports", icon: MessageSquareWarning },
  { to: "/audit", key: "audit", icon: ScrollText }
];

export function AppLayout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <strong>{t("app.name")}</strong>
            <span>{t("app.subtitle")}</span>
          </div>
        </div>
        <nav className="side-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} end={item.to === "/"}>
                <Icon size={18} aria-hidden="true" />
                <span>{t(`nav.${item.key}`)}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div className="operator">
            <span>{user?.name}</span>
            <small>{user?.email}</small>
          </div>
          <LanguageSwitcher />
          <Button className="logout-button" onClick={logout} type="button" variant="ghost">
            <LogOut size={16} aria-hidden="true" />
            <span>{t("common.logout")}</span>
          </Button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
