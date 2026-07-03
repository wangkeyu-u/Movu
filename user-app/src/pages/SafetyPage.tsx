import { Button, Card } from "@movu/ui";
import { LocateFixed, Siren } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import { AccessNotice } from "../components/AccessNotice";
import { Field } from "../components/Field";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useDepthTilt } from "../components/useDepthTilt";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";
import { useResource } from "./useResource";

export function SafetyPage() {
  const { user } = useAuth();
  const trips = useResource(() => api.trips().catch(() => api.rideRequests().then(() => [])), []);
  const { t } = useTranslation();
  const accessIssue = getAccessIssue(user);
  const [tripId, setTripId] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const heroDepth = useDepthTilt(3);

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setError(t("common.locationUnavailable"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(String(roundCoordinate(position.coords.latitude)));
        setLongitude(String(roundCoordinate(position.coords.longitude)));
      },
      () => setError(t("map.readFailed")),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  async function sendLocation(event: React.FormEvent) {
    event.preventDefault();
    await run(async () => {
      await api.sendLocation({
        trip_id: Number(tripId),
        latitude: Number(latitude),
        longitude: Number(longitude)
      });
      setMessage(t("safety.locationShared"));
    });
  }

  async function triggerSos() {
    await run(async () => {
      await api.triggerSos({
        trip_id: Number(tripId),
        latitude: Number(latitude),
        longitude: Number(longitude)
      });
      setMessage(t("safety.sosSent"));
    });
  }

  async function run(action: () => Promise<void>) {
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.somethingWrong"));
    }
  }

  return (
    <div className="page-stack">
      <Card className="safety-hero depth-surface" tone="dark" {...heroDepth}>
        <div>
          <span className="quiet-label">{t("safety.label")}</span>
          <h1>{t("safety.title")}</h1>
          <p>{t("safety.subtitle")}</p>
        </div>
        <img src="/assets/images/illustration-car-navigation.jpg" alt="" aria-hidden="true" />
        <Siren size={34} aria-hidden="true" />
      </Card>

      {accessIssue ? (
        <AccessNotice issue={accessIssue} />
      ) : (
        <Card as="form" className="records-panel form-stack" onSubmit={sendLocation}>
          <Field label={t("common.tripId")} inputMode="numeric" value={tripId} onChange={(event) => setTripId(event.target.value)} required />
          <div className="split-fields">
            <Field label={t("common.latitude")} inputMode="decimal" value={latitude} onChange={(event) => setLatitude(event.target.value)} required />
            <Field label={t("common.longitude")} inputMode="decimal" value={longitude} onChange={(event) => setLongitude(event.target.value)} required />
          </div>
          <div className="button-row">
            <Button variant="secondary" type="button" onClick={useCurrentLocation}>
              <LocateFixed size={17} aria-hidden="true" />
              {t("common.useCurrent")}
            </Button>
            <Button type="submit">
              {t("safety.shareLocation")}
            </Button>
          </div>
          <Button variant="danger" type="button" onClick={triggerSos}>
            {t("safety.sendSos")}
          </Button>
        </Card>
      )}

      <Toast message={error} tone="error" />
      <Toast message={message} tone="success" />

      <Card className="records-panel">
        <h2>{t("safety.activeTrips")}</h2>
        {trips.data?.map((trip) => (
          <Button className="trip-select" variant="ghost" type="button" key={trip.trip_id} onClick={() => setTripId(String(trip.trip_id))}>
            <span>{t("safety.tripNumber", { id: trip.trip_id })}</span>
            <StatusPill value={trip.status} />
          </Button>
        ))}
        {!trips.loading && !trips.data?.length && <p className="empty-copy">{t("safety.empty")}</p>}
      </Card>
    </div>
  );
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000000) / 1000000;
}
