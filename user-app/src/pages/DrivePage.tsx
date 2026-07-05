import { Button, Card } from "@movu/ui";
import { CarFront, Clock3, ParkingCircle, RefreshCw, Route } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Match, Point } from "../api/types";
import { AccessNotice } from "../components/AccessNotice";
import { CampusMapPicker } from "../components/CampusMapPicker";
import { ExperienceHero } from "../components/ExperienceHero";
import { Field } from "../components/Field";
import { MatchInsightCard } from "../components/MatchInsightCard";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { TripNetworkPanel } from "../components/TripNetworkPanel";
import { WorkflowNav } from "../components/WorkflowNav";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";
import { CAMPUS_TIME_ZONE, fromLocalInputValue, formatDateTime, toLocalInputValue } from "../utils/format";
import { formatPoint } from "../utils/geo";
import { useResource } from "./useResource";

interface DrivePageProps {
  mode?: "trip" | "garage" | "trips";
}

export function DrivePage({ mode = "trip" }: DrivePageProps) {
  const { user } = useAuth();
  const isDriver = user?.role === "driver";
  const vehicles = useResource(() => api.vehicles(), [], { enabled: isDriver, disabledValue: [] });
  const trips = useResource(() => api.trips(), [], { enabled: isDriver, disabledValue: [] });
  const networkTrips = useResource(() => api.networkTrips(), [], { enabled: isDriver, disabledValue: [] });
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
        departure_time_timezone: CAMPUS_TIME_ZONE,
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

  async function updateTripStatus(tripId: number, status: "ongoing" | "completed" | "cancelled", successMessage: string) {
    await run(async () => {
      await api.updateTripStatus(tripId, status);
      setMessage(successMessage);
      trips.reload();
      networkTrips.reload();
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
      <ExperienceHero
        title={t("drive.title")}
        subtitle={t("drive.subtitle")}
        label={t("drive.heroLabel")}
        image="/assets/images/bg-campus-path-students.jpg"
        icon={<CarFront size={28} />}
        variant="drive"
      />

      <WorkflowNav
        label={t("drive.workflow")}
        items={[
          { to: "/", label: t("drive.tripTab"), icon: <Route size={17} aria-hidden="true" />, end: true },
          { to: "/driver/garage", label: t("drive.garageTab"), icon: <ParkingCircle size={17} aria-hidden="true" /> },
          { to: "/driver/trips", label: t("drive.tripsTab"), icon: <Clock3 size={17} aria-hidden="true" /> }
        ]}
      />

      {!isDriver && <AccessNotice issue="driver_only" />}

      {mode === "garage" && isDriver && <Card className="records-panel">
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
      </Card>}

      {mode === "trip" && isDriver && !accessIssue && (
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
          <Field label={`${t("drive.departureTime")} (${CAMPUS_TIME_ZONE})`} type="datetime-local" value={departureTime} onChange={(event) => setDepartureTime(event.target.value)} required />
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

      {mode === "trip" && isDriver && accessIssue && <AccessNotice issue={accessIssue} />}

      <Toast message={error} tone="error" />
      <Toast message={message} tone="success" />

      {mode === "trips" && isDriver && <Card className="records-panel">
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
                  <Button variant="ghost" type="button" onClick={() => updateTripStatus(trip.trip_id, "cancelled", t("drive.tripCancelled"))}>
                    {t("common.cancel")}
                  </Button>
                )}
                {trip.status === "matched" && (
                  <Button variant="primary" type="button" onClick={() => updateTripStatus(trip.trip_id, "ongoing", t("drive.tripStarted"))}>
                    {t("drive.startTrip")}
                  </Button>
                )}
                {trip.status === "ongoing" && (
                  <Button variant="secondary" type="button" onClick={() => updateTripStatus(trip.trip_id, "completed", t("drive.tripCompleted"))}>
                    {t("drive.completeTrip")}
                  </Button>
                )}
              </div>
            )}
            {!accessIssue && matches[trip.trip_id]?.map((match) => (
              <MatchInsightCard
                key={match.match_id}
                match={match}
                label={t("drive.requestNumber", { id: match.request_id })}
                actionLabel={t("common.reject")}
                onAction={() => reject(match.match_id)}
              />
            ))}
          </Card>
        ))}
      </Card>}

      {mode === "trips" && isDriver && networkTrips.data
        ?.filter((trip) => ["matched", "ongoing", "completed"].includes(trip.status))
        .map((trip) => <TripNetworkPanel key={trip.trip_id} trip={trip} />)}
    </div>
  );
}
