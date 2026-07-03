import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "./useResource";

interface DashboardData {
  users: number;
  vehicles: number;
  requests: number;
  trips: number;
  matches: number;
  payments: number;
  sos: number;
  reports: number;
  pendingUsers: number;
  pendingVehicles: number;
  newSos: number;
}

export function DashboardPage() {
  const { t } = useTranslation();
  const loader = useCallback(async (): Promise<DashboardData> => {
    const [users, vehicles, requests, trips, matches, payments, sos, reports] = await Promise.all([
      api.users(),
      api.vehicles(),
      api.rideRequests(),
      api.trips(),
      api.matches(),
      api.payments(),
      api.sosEvents(),
      api.reports()
    ]);
    return {
      users: users.length,
      vehicles: vehicles.length,
      requests: requests.length,
      trips: trips.length,
      matches: matches.length,
      payments: payments.length,
      sos: sos.length,
      reports: reports.length,
      pendingUsers: users.filter((user) => user.verification_status === "pending").length,
      pendingVehicles: vehicles.filter((vehicle) => vehicle.verification_status === "pending").length,
      newSos: sos.filter((event) => event.status === "new").length
    };
  }, []);
  const { data, loading, error } = useResource(loader);

  const metrics = [
    ["dashboard.users", data?.users],
    ["dashboard.vehicles", data?.vehicles],
    ["dashboard.requests", data?.requests],
    ["dashboard.trips", data?.trips],
    ["dashboard.matches", data?.matches],
    ["dashboard.payments", data?.payments],
    ["dashboard.sos", data?.sos],
    ["dashboard.reports", data?.reports]
  ] as const;

  return (
    <PageShell title={t("dashboard.title")} subtitle={t("dashboard.subtitle")}>
      {loading && <div className="skeleton-grid" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <>
          <div className="metric-grid">
            {metrics.map(([label, value]) => (
              <article className="metric-tile" key={label}>
                <span>{t(label)}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
          <section className="attention-panel">
            <div>
              <h2>{t("dashboard.attention")}</h2>
              <p>{t("dashboard.attentionCopy")}</p>
            </div>
            <div className="attention-stack">
              <span>
                {t("users.verification")} <StatusBadge value="pending" /> {data.pendingUsers}
              </span>
              <span>
                {t("vehicles.verification")} <StatusBadge value="pending" /> {data.pendingVehicles}
              </span>
              <span>
                {t("sos.title")} <StatusBadge value="new" /> {data.newSos}
              </span>
            </div>
          </section>
        </>
      )}
    </PageShell>
  );
}
