import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Match } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function MatchesPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<Match[]>(useCallback(() => api.matches(), []));

  return (
    <PageShell title={t("matches.title")} subtitle={t("matches.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "trip", header: t("matches.trip"), render: (match) => `#${match.trip_id}` },
            { key: "request", header: t("matches.request"), render: (match) => `#${match.request_id}` },
            { key: "rider", header: t("matches.rider"), render: (match) => `#${match.rider_id}` },
            { key: "score", header: t("matches.score"), render: (match) => match.match_score.toFixed(2) },
            { key: "status", header: t("common.status"), render: (match) => <StatusBadge value={match.status} /> },
            { key: "created", header: t("common.createdAt"), render: (match) => formatDate(match.created_at) }
          ]}
        />
      )}
    </PageShell>
  );
}
