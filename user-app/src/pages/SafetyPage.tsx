import { Button, Card } from "@movu/ui";
import { LocateFixed, PhoneCall, Siren, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Trip } from "../api/types";
import { AccessNotice } from "../components/AccessNotice";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useDepthTilt } from "../components/useDepthTilt";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";
import { formatDateTime } from "../utils/format";
import { useResource } from "./useResource";

interface PendingSos {
  trip: Trip;
  latitude: number;
  longitude: number;
}

export function SafetyPage() {
  const { user } = useAuth();
  const { i18n, t } = useTranslation();
  const accessIssue = getAccessIssue(user);
  const currentTrip = useResource(() => api.currentSafetyTrip(), []);
  const [pendingSos, setPendingSos] = useState<PendingSos | null>(null);
  const [locating, setLocating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const heroDepth = useDepthTilt(2.2);

  async function locateNow(): Promise<{ latitude: number; longitude: number }> {
    if (!navigator.geolocation) {
      throw new Error(t("common.locationUnavailable"));
    }
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: roundCoordinate(position.coords.latitude),
            longitude: roundCoordinate(position.coords.longitude)
          });
        },
        () => reject(new Error(t("map.readFailed"))),
        { enableHighAccuracy: true, timeout: 6000, maximumAge: 0 }
      );
    });
  }

  async function prepareSos() {
    setError(null);
    setMessage(null);
    setLocating(true);
    try {
      const trip = currentTrip.data ?? (await api.currentSafetyTrip());
      const location = await locateNow();
      setPendingSos({ trip, ...location });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("safety.noActiveTrip"));
    } finally {
      setLocating(false);
    }
  }

  async function confirmSos() {
    if (!pendingSos) return;
    await run(async () => {
      await api.triggerSos({
        trip_id: pendingSos.trip.trip_id,
        latitude: pendingSos.latitude,
        longitude: pendingSos.longitude
      });
      setPendingSos(null);
      setMessage(t("safety.sosSent"));
    });
  }

  async function shareDriverLocation() {
    const trip = currentTrip.data;
    if (!trip) return;
    await run(async () => {
      const location = await locateNow();
      await api.sendLocation({
        trip_id: trip.trip_id,
        latitude: location.latitude,
        longitude: location.longitude
      });
      setMessage(t("safety.locationShared"));
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
        <Card className="sos-console">
          <div className="sos-trip-card">
            <span>{t("safety.currentTrip")}</span>
            {currentTrip.data ? (
              <>
                <strong>{currentTrip.data.origin} {t("common.routeJoiner")} {currentTrip.data.destination}</strong>
                <small>{formatDateTime(currentTrip.data.departure_time, i18n.language === "en" ? "en-MY" : i18n.language)}</small>
                <StatusPill value={currentTrip.data.status} />
              </>
            ) : (
              <strong>{currentTrip.loading ? t("safety.findingTrip") : t("safety.noActiveTrip")}</strong>
            )}
          </div>

          <Button className="sos-panic-button" variant="danger" type="button" onClick={prepareSos} disabled={locating || currentTrip.loading}>
            <Siren size={26} aria-hidden="true" />
            {locating ? t("safety.locating") : t("safety.sendSos")}
          </Button>

          {user?.role === "driver" && currentTrip.data?.status === "ongoing" && (
            <Button variant="secondary" type="button" onClick={shareDriverLocation}>
              <LocateFixed size={17} aria-hidden="true" />
              {t("safety.shareLocation")}
            </Button>
          )}
        </Card>
      )}

      {pendingSos && (
        <div className="confirm-sheet" role="dialog" aria-modal="true" aria-label={t("safety.confirmTitle")}>
          <Card className="confirm-panel">
            <Button className="sheet-close" variant="icon" type="button" onClick={() => setPendingSos(null)} aria-label={t("common.cancel")}>
              <X size={18} aria-hidden="true" />
            </Button>
            <Siren size={32} aria-hidden="true" />
            <h2>{t("safety.confirmTitle")}</h2>
            <p>{t("safety.confirmBody", { tripId: pendingSos.trip.trip_id })}</p>
            <div className="sos-coordinate">
              <span>{pendingSos.latitude}</span>
              <span>{pendingSos.longitude}</span>
            </div>
            <Button variant="danger" type="button" onClick={confirmSos} wide>
              <PhoneCall size={18} aria-hidden="true" />
              {t("safety.confirmCall")}
            </Button>
          </Card>
        </div>
      )}

      <Toast message={error} tone="error" />
      <Toast message={message} tone="success" />
    </div>
  );
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000000) / 1000000;
}
