import { Button } from "@movu/ui";
import { Bell, Car, Home, LifeBuoy, LogOut, Route, UserRound } from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavLink, Outlet } from "react-router-dom";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { useAuth } from "./AuthProvider";

const navItems = [
  { to: "/", labelKey: "nav.home", icon: Home },
  { to: "/ride", labelKey: "nav.ride", icon: Route },
  { to: "/drive", labelKey: "nav.drive", icon: Car },
  { to: "/safety", labelKey: "nav.safety", icon: LifeBuoy },
  { to: "/account", labelKey: "nav.account", icon: UserRound }
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  return (
    <div className="mobile-frame">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark">M</div>
          <div>
            <strong>MovU</strong>
            <span>{t("app.tagline")}</span>
          </div>
        </div>
        <div className="header-actions">
          <LanguageSwitcher />
          <Button variant="icon" type="button" aria-label={t("common.notifications")}>
            <Bell size={18} aria-hidden="true" />
          </Button>
          <Button variant="icon" type="button" onClick={logout} aria-label={t("common.logout")}>
            <LogOut size={18} aria-hidden="true" />
          </Button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="bottom-nav" aria-label={t("nav.primary")}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              <Icon size={20} aria-hidden="true" />
              <span>{t(item.labelKey)}</span>
            </NavLink>
          );
        })}
      </nav>
      <div className="session-chip">{t(`roles.${user?.role}`, { defaultValue: user?.role })}</div>
    </div>
  );
}
