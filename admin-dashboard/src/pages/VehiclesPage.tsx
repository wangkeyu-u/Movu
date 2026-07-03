import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Vehicle } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function VehiclesPage() {
  const { t } = useTranslation();
  const { data, loading, error, reload } = useResource<Vehicle[]>(useCallback(() => api.vehicles(), []));

  async function run(action: Promise<unknown>) {
    await action;
    reload();
  }

  return (
    <PageShell title={t("vehicles.title")} subtitle={t("vehicles.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "plate", header: t("vehicles.plate"), render: (vehicle) => <strong>{vehicle.plate_number}</strong> },
            { key: "model", header: t("vehicles.model"), render: (vehicle) => vehicle.vehicle_model },
            { key: "driver", header: t("vehicles.driver"), render: (vehicle) => `#${vehicle.driver_id}` },
            { key: "seats", header: t("vehicles.seats"), render: (vehicle) => vehicle.seat_count },
            {
              key: "verification",
              header: t("vehicles.verification"),
              render: (vehicle) => <StatusBadge value={vehicle.verification_status} />
            },
            { key: "created", header: t("common.createdAt"), render: (vehicle) => formatDate(vehicle.created_at) },
            {
              key: "actions",
              header: t("common.actions"),
              render: (vehicle) => (
                <div className="action-row">
                  <ActionButton onClick={() => run(api.verifyVehicle(vehicle.vehicle_id, "approved"))}>
                    {t("common.approve")}
                  </ActionButton>
                  <ActionButton onClick={() => run(api.verifyVehicle(vehicle.vehicle_id, "rejected"))}>
                    {t("common.reject")}
                  </ActionButton>
                </div>
              )
            }
          ]}
        />
      )}
    </PageShell>
  );
}
