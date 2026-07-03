import { Button, Card } from "@movu/ui";
import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Match, Point } from "../api/types";
import { AccessNotice } from "../components/AccessNotice";
import { CampusMapPicker } from "../components/CampusMapPicker";
import { Field } from "../components/Field";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useDepthTilt } from "../components/useDepthTilt";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";
import { fromLocalInputValue, formatDateTime, toLocalInputValue } from "../utils/format";
import { formatPoint } from "../utils/geo";
import { useResource } from "./useResource";

export function DrivePage() {
  const { user } = useAuth();
  const vehicles = useResource(() => api.vehicles(), []);
  const trips = useResource(() => api.trips(), []);
  const { i18n, t } = useTranslation();
  const accessIssue = getAccessIssue(user);
  const approvedSeats = useMemo(
    () => Math.max(0, ...(vehicles.data ?? []).filter((vehicle) => vehicle.verification_status === "approved").map((vehicle) => vehicle.seat_count)),
    [vehicles.data]
  );
  const [plateNumber, setPlateNumber] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [seatCount, setSeatCount] = useState(4);
  const [origin, setOrigin] = useState<Point | null>(null);
  const [destination, setDestination] = useState<Point | null>(null);
  const [departureTime, setDepartureTime] = useState(toLocalInputValue());
  const [availableSeats, setAvailableSeats] = useState(1);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<number, Match[]>>({});
  const headingDepth = useDepthTilt(3);

  async function registerVehicle(event: React.FormEvent) {
    event.preventDefault();
    await run(async () => {
      await api.createVehicle({ plate_number: plateNumber, vehicle_model: vehicleModel, seat_count: seatCount });
      setMessage(t("drive.vehicleSubmitted"));
      vehicles.reload();
    });
  }

  async function createTrip(event: React.FormEvent) {
    event.preventDefault();
    if (!origin || !destination) {
      setError(t("ride.chooseBoth"));
      return;
    }
    await run(async () => {
      await api.createTrip({
        origin: origin.label,
        destination: destination.label,
        origin_latitude: origin.latitude,
        origin_longitude: origin.longitude,
        destination_latitude: destination.latitude,
        destination_longitude: destination.longitude,
        departure_time: fromLocalInputValue(departureTime),
        available_seats: availableSeats
      });
      setMessage(t("drive.posted"));
      trips.reload();
    });
  }

  async function loadRecommendations(tripId: number) {
    await run(async () => {
      const recommendations = await api.tripRecommendations(tripId);
      setMatches((prev) => ({ ...prev, [tripId]: recommendations }));
    });
  }

  async function reject(matchId: number) {
    await run(async () => {
      await api.rejectMatch(matchId);
      setMessage(t("drive.matchRejected"));
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

  function updatePoint(target: "origin" | "destination", point: Point) {
    if (target === "origin") setOrigin(point);
    else setDestination(point);
  }

  return (
    <div className="page-stack">
      <section className="section-heading visual-heading drive-heading depth-surface" {...headingDepth}>
        <div>
          <h1>{t("drive.title")}</h1>
          <p>{t("drive.subtitle")}</p>
        </div>
        <img src="/assets/images/ill-carpooling-public-domain.png" alt="" aria-hidden="true" />
      </section>

      <Card className="records-panel">
        <div className="panel-title">
          <h2>{t("drive.vehicles")}</h2>
          <Button variant="icon" type="button" onClick={vehicles.reload} aria-label={t("common.refreshVehicles")}>
            <RefreshCw size={17} aria-hidden="true" />
          </Button>
        </div>
        {vehicles.data?.map((vehicle) => (
          <Card as="article" tone="strong" className="record-card compact" key={vehicle.vehicle_id}>
            <strong>{vehicle.plate_number}</strong>
            <span>{vehicle.vehicle_model} · {vehicle.seat_count} {t("common.seats")}</span>
            <StatusPill value={vehicle.verification_status} />
          </Card>
        ))}
        {accessIssue ? (
          <AccessNotice issue={accessIssue} />
        ) : (
          <form className="form-stack" onSubmit={registerVehicle}>
            <Field label={t("drive.plateNumber")} value={plateNumber} onChange={(event) => setPlateNumber(event.target.value)} required />
            <Field label={t("drive.vehicleModel")} value={vehicleModel} onChange={(event) => setVehicleModel(event.target.value)} required />
            <Field label={t("drive.seatCount")} type="number" min={1} max={8} value={seatCount} onChange={(event) => setSeatCount(Number(event.target.value))} required />
            <Button variant="secondary" type="submit">
              {t("drive.submitVehicle")}
            </Button>
          </form>
        )}
      </Card>

      {!accessIssue && (
        <Card as="form" className="ride-form" onSubmit={createTrip}>
          <div className="panel-title">
            <h2>{t("drive.postTrip")}</h2>
            <StatusPill value={approvedSeats > 0 ? "approved" : "pending"} />
          </div>
          <CampusMapPicker origin={origin} destination={destination} onChange={updatePoint} />
          <div className="route-summary">
            <div>
              <span>{t("common.origin")}</span>
              <strong>{formatPoint(origin, t("map.chooseOnMap"))}</strong>
            </div>
            <div>
              <span>{t("common.destination")}</span>
              <strong>{formatPoint(destination, t("map.chooseOnMap"))}</strong>
            </div>
          </div>
          <Field label={t("drive.departureTime")} type="datetime-local" value={departureTime} onChange={(event) => setDepartureTime(event.target.value)} required />
          <Field
            label={t("common.availableSeats")}
            type="number"
            min={1}
            max={Math.max(1, approvedSeats)}
            value={availableSeats}
            onChange={(event) => setAvailableSeats(Number(event.target.value))}
            required
          />
          <Button disabled={approvedSeats === 0} type="submit">
            {t("drive.postTrip")}
          </Button>
        </Card>
      )}

      <Toast message={error} tone="error" />
      <Toast message={message} tone="success" />

      <Card className="records-panel">
        <div className="panel-title">
          <h2>{t("drive.myTrips")}</h2>
          <Button variant="icon" type="button" onClick={trips.reload} aria-label={t("common.refreshTrips")}>
            <RefreshCw size={17} aria-hidden="true" />
          </Button>
        </div>
        {trips.data?.map((trip) => (
          <Card as="article" tone="strong" className="record-card" key={trip.trip_id}>
            <div>
              <strong>{trip.origin} {t("common.routeJoiner")} {trip.destination}</strong>
              <span>{formatDateTime(trip.departure_time, i18n.language === "en" ? "en-MY" : i18n.language)}</span>
            </div>
            <div className="record-meta">
              <StatusPill value={trip.status} />
              <span>{trip.available_seats}/{trip.total_seats} {t("common.seats")}</span>
            </div>
            {!accessIssue && (
              <div className="button-row">
                <Button variant="secondary" type="button" onClick={() => loadRecommendations(trip.trip_id)}>
                  {t("drive.riderMatches")}
                </Button>
                {trip.status === "posted" && (
                  <Button variant="ghost" type="button" onClick={() => api.updateTripStatus(trip.trip_id, "cancelled").then(trips.reload)}>
                    {t("common.cancel")}
                  </Button>
                )}
              </div>
            )}
            {!accessIssue && matches[trip.trip_id]?.map((match) => (
              <div className="match-row" key={match.match_id}>
                <span>{t("drive.requestNumber", { id: match.request_id })}</span>
                <strong>{Math.round(match.match_score)}%</strong>
                <Button variant="secondary" type="button" onClick={() => reject(match.match_id)}>
                  {t("common.reject")}
                </Button>
              </div>
            ))}
          </Card>
        ))}
      </Card>
    </div>
  );
}
