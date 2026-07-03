import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { SOSEvent } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function SOSEventsPage() {
  const { t } = useTranslation();
  const { data, loading, error, reload } = useResource<SOSEvent[]>(useCallback(() => api.sosEvents(), []));

  async function run(action: Promise<unknown>) {
    await action;
    reload();
  }

  return (
    <PageShell title={t("sos.title")} subtitle={t("sos.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "user", header: t("sos.user"), render: (event) => `#${event.user_id}` },
            { key: "trip", header: t("sos.trip"), render: (event) => `#${event.trip_id}` },
            { key: "location", header: t("sos.location"), render: (event) => `${event.latitude}, ${event.longitude}` },
            { key: "triggered", header: t("sos.triggered"), render: (event) => formatDate(event.triggered_time) },
            { key: "resolved", header: t("sos.resolved"), render: (event) => formatDate(event.resolved_time) },
            { key: "status", header: t("common.status"), render: (event) => <StatusBadge value={event.status} /> },
            {
              key: "actions",
              header: t("common.actions"),
              render: (event) => (
                <div className="action-row">
                  <ActionButton onClick={() => run(api.updateSos(event.sos_id, "reviewing"))}>{t("common.review")}</ActionButton>
                  <ActionButton onClick={() => run(api.updateSos(event.sos_id, "resolved"))}>{t("common.resolve")}</ActionButton>
                  <ActionButton onClick={() => run(api.updateSos(event.sos_id, "false_alarm"))}>
                    {t("common.falseAlarm")}
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
