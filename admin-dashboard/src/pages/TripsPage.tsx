import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Trip } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function TripsPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<Trip[]>(useCallback(() => api.trips(), []));

  return (
    <PageShell title={t("trips.title")} subtitle={t("trips.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "driver", header: t("trips.driver"), render: (trip) => `#${trip.driver_id}` },
            { key: "origin", header: t("trips.origin"), render: (trip) => trip.origin },
            { key: "destination", header: t("trips.destination"), render: (trip) => trip.destination },
            { key: "time", header: t("trips.time"), render: (trip) => formatDate(trip.departure_time) },
            { key: "seats", header: t("trips.seats"), render: (trip) => `${trip.available_seats}/${trip.total_seats}` },
            { key: "status", header: t("common.status"), render: (trip) => <StatusBadge value={trip.status} /> }
          ]}
        />
      )}
    </PageShell>
  );
}
