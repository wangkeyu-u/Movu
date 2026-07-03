import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { AuditLog } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function AuditLogsPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<AuditLog[]>(useCallback(() => api.auditLogs(), []));

  return (
    <PageShell title={t("audit.title")} subtitle={t("audit.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "actor", header: t("audit.actor"), render: (log) => log.actor_user_id ?? t("common.emptyValue") },
            { key: "action", header: t("audit.action"), render: (log) => log.action },
            { key: "entity", header: t("audit.entity"), render: (log) => `${log.entity_type} #${log.entity_id}` },
            { key: "ip", header: t("audit.ip"), render: (log) => log.ip_address ?? t("common.emptyValue") },
            { key: "metadata", header: t("audit.metadata"), render: (log) => log.metadata_json ?? t("common.emptyValue") },
            { key: "created", header: t("common.createdAt"), render: (log) => formatDate(log.created_at) }
          ]}
        />
      )}
    </PageShell>
  );
}
