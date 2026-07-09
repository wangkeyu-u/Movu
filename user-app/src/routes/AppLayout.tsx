import { Button } from "@movu/ui";
import { Clock3, Home, LogOut, ParkingCircle, Route, UserRound } from "lucide-react";
import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, Outlet } from "react-router-dom";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { NotificationTray } from "../components/NotificationTray";
import { useAuth } from "./AuthProvider";

const riderNavItems = [
  { to: "/", labelKey: "nav.home", icon: Home },
  { to: "/ride/activity", labelKey: "nav.activity", icon: Clock3 },
  { to: "/account", labelKey: "nav.account", icon: UserRound }
];

const driverNavItems = [
  { to: "/", labelKey: "nav.home", icon: Home },
  { to: "/driver/trips", labelKey: "nav.trips", icon: Route },
  { to: "/driver/garage", labelKey: "nav.garage", icon: ParkingCircle },
  { to: "/account", labelKey: "nav.account", icon: UserRound }
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const navItems = user?.role === "driver" ? driverNavItems : riderNavItems;

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
          <NotificationTray />
          <Button variant="icon" type="button" onClick={logout} aria-label={t("common.logout")}>
            <LogOut size={18} aria-hidden="true" />
          </Button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="bottom-nav" style={{ "--nav-count": navItems.length } as CSSProperties} aria-label={t("nav.primary")}>
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
