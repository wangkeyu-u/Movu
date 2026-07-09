import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Input } from "@movu/ui";

import { api, sosSocketUrl } from "../api/client";
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
  const [liveAlert, setLiveAlert] = useState<SOSEvent | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});

  async function updateStatus(event: SOSEvent, status: "reviewing" | "resolved" | "false_alarm") {
    await api.updateSos(event.sos_id, status, notes[event.sos_id]);
    reload();
  }

  useEffect(() => {
    const url = sosSocketUrl();
    if (!url) return undefined;
    const socket = new WebSocket(url);
    socket.onmessage = (event) => {
      try {
        const sosEvent = JSON.parse(event.data) as SOSEvent;
        setLiveAlert(sosEvent);
        reload();
      } catch {
        setLiveAlert(null);
      }
    };
    return () => socket.close();
  }, [reload]);

  return (
    <PageShell title={t("sos.title")} subtitle={t("sos.subtitle")}>
      {liveAlert && (
        <section className="sos-live-alert" role="status" aria-live="assertive">
          <div>
            <strong>{t("sos.liveAlert")}</strong>
            <span>{t("sos.liveAlertBody", { tripId: liveAlert.trip_id, userId: liveAlert.user_id })}</span>
          </div>
          <a href={`https://www.openstreetmap.org/?mlat=${liveAlert.latitude}&mlon=${liveAlert.longitude}#map=17/${liveAlert.latitude}/${liveAlert.longitude}`} target="_blank" rel="noreferrer">
            {t("sos.openMap")}
          </a>
        </section>
      )}
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
            { key: "assigned", header: t("sos.assigned"), render: (event) => event.assigned_admin_id ? `#${event.assigned_admin_id}` : t("common.emptyValue") },
            {
              key: "timeline",
              header: t("sos.timeline"),
              render: (event) => (
                <div className="sos-timeline-cell">
                  <span>{event.status_updated_at ? formatDate(event.status_updated_at) : t("common.emptyValue")}</span>
                  <small>{event.response_note || t("sos.noResponseNote")}</small>
                </div>
              )
            },
            { key: "status", header: t("common.status"), render: (event) => <StatusBadge value={event.status} /> },
            {
              key: "actions",
              header: t("common.actions"),
              render: (event) => (
                <div className="sos-response-controls">
                  <Input
                    value={notes[event.sos_id] ?? event.response_note ?? ""}
                    onChange={(inputEvent) => setNotes((current) => ({ ...current, [event.sos_id]: inputEvent.target.value }))}
                    placeholder={t("sos.notePlaceholder")}
                    aria-label={t("sos.responseNote")}
                  />
                  <div className="action-row">
                    <ActionButton onClick={() => updateStatus(event, "reviewing")}>{t("common.review")}</ActionButton>
                    <ActionButton onClick={() => updateStatus(event, "resolved")}>{t("common.resolve")}</ActionButton>
                    <ActionButton onClick={() => updateStatus(event, "false_alarm")}>
                      {t("common.falseAlarm")}
                    </ActionButton>
                    <a className="map-action-link" href={`https://www.openstreetmap.org/?mlat=${event.latitude}&mlon=${event.longitude}#map=17/${event.latitude}/${event.longitude}`} target="_blank" rel="noreferrer">
                      {t("sos.openMap")}
                    </a>
                  </div>
                </div>
              )
            }
          ]}
        />
      )}
    </PageShell>
  );
}
