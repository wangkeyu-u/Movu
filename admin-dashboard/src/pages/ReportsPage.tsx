import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { RatingReport } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function ReportsPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<RatingReport[]>(useCallback(() => api.reports(), []));

  return (
    <PageShell title={t("reports.title")} subtitle={t("reports.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "from", header: t("reports.from"), render: (record) => `#${record.from_user_id}` },
            { key: "to", header: t("reports.to"), render: (record) => `#${record.to_user_id}` },
            { key: "trip", header: t("reports.trip"), render: (record) => `#${record.trip_id}` },
            { key: "score", header: t("reports.score"), render: (record) => record.score ?? t("common.emptyValue") },
            {
              key: "type",
              header: t("reports.type"),
              render: (record) => (record.report_type ? t(`reportTypes.${record.report_type}`) : t("common.emptyValue"))
            },
            { key: "comment", header: t("reports.comment"), render: (record) => record.comment ?? t("common.emptyValue") },
            { key: "created", header: t("common.createdAt"), render: (record) => formatDate(record.created_at) }
          ]}
        />
      )}
    </PageShell>
  );
}
