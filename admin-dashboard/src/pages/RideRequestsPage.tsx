import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { RideRequest } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function RideRequestsPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<RideRequest[]>(useCallback(() => api.rideRequests(), []));

  return (
    <PageShell title={t("rideRequests.title")} subtitle={t("rideRequests.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "rider", header: t("rideRequests.rider"), render: (request) => `#${request.rider_id}` },
            { key: "origin", header: t("rideRequests.origin"), render: (request) => request.origin },
            { key: "destination", header: t("rideRequests.destination"), render: (request) => request.destination },
            { key: "time", header: t("rideRequests.time"), render: (request) => formatDate(request.preferred_time) },
            { key: "passengers", header: t("rideRequests.passengers"), render: (request) => request.passenger_count },
            { key: "gender", header: t("rideRequests.gender"), render: (request) => t(`genderPreference.${request.gender_preference}`) },
            { key: "distance", header: t("rideRequests.distance"), render: (request) => request.distance_km ?? t("common.emptyValue") },
            { key: "status", header: t("common.status"), render: (request) => <StatusBadge value={request.status} /> }
          ]}
        />
      )}
    </PageShell>
  );
}
