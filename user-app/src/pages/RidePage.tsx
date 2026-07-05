import { Button, Card } from "@movu/ui";
import { Clock3, MapPinned, RefreshCw, Route } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Match, Point } from "../api/types";
import { AccessNotice } from "../components/AccessNotice";
import { CampusMapPicker } from "../components/CampusMapPicker";
import { ExperienceHero } from "../components/ExperienceHero";
import { Field } from "../components/Field";
import { MatchInsightCard } from "../components/MatchInsightCard";
import { SelectField } from "../components/SelectField";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { TripNetworkPanel } from "../components/TripNetworkPanel";
import { WorkflowNav } from "../components/WorkflowNav";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";
import { CAMPUS_TIME_ZONE, fromLocalInputValue, formatDateTime, toLocalInputValue } from "../utils/format";
import { formatPoint } from "../utils/geo";
import { useResource } from "./useResource";

interface RidePageProps {
  mode?: "book" | "activity";
}

export function RidePage({ mode = "book" }: RidePageProps) {
  const { user } = useAuth();
  const { data, loading, error, reload } = useResource(() => api.rideRequests(), []);
  const networkTrips = useResource(() => api.networkTrips(), []);
  const { i18n, t } = useTranslation();
  const accessIssue = getAccessIssue(user);
  const [origin, setOrigin] = useState<Point | null>(null);
  const [destination, setDestination] = useState<Point | null>(null);
  const [preferredTime, setPreferredTime] = useState(toLocalInputValue());
  const [passengerCount, setPassengerCount] = useState(1);
  const [genderPreference, setGenderPreference] = useState("none");
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<number, Match[]>>({});

  function updatePoint(target: "origin" | "destination", point: Point) {
    if (target === "origin") setOrigin(point);
    else setDestination(point);
  }

  async function createRequest(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    setMessage(null);
    if (!origin || !destination) {
      setFormError(t("ride.chooseBoth"));
      return;
    }
    try {
      const request = await api.createRideRequest({
        origin: origin.label,
        destination: destination.label,
        origin_latitude: origin.latitude,
        origin_longitude: origin.longitude,
        destination_latitude: destination.latitude,
        destination_longitude: destination.longitude,
        preferred_time: fromLocalInputValue(preferredTime),
        preferred_time_timezone: CAMPUS_TIME_ZONE,
        passenger_count: passengerCount,
        gender_preference: genderPreference
      });
      try {
        const assignedMatch = await api.autoAssignRequest(request.request_id);
        setMessage(t("ride.assigned", { tripId: assignedMatch.trip_id }));
      } catch {
        setMessage(t("ride.created"));
      }
      reload();
      networkTrips.reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : t("ride.createFailed"));
    }
  }

  async function loadRecommendations(requestId: number) {
    setFormError(null);
    try {
      const recommendations = await api.requestRecommendations(requestId);
      setMatches((prev) => ({ ...prev, [requestId]: recommendations }));
    } catch (err) {
      setFormError(err instanceof Error ? err.message : t("ride.loadFailed"));
    }
  }

  async function confirm(matchId: number) {
    await api.confirmMatch(matchId);
    setMessage(t("ride.confirmed"));
    reload();
  }

  return (
    <div className="page-stack">
      <ExperienceHero
        title={t("ride.title")}
        subtitle={t("ride.subtitle")}
        label={t("ride.heroLabel")}
        image="/assets/images/bg-lakeside-building.jpg"
        icon={<MapPinned size={28} />}
      />

      <WorkflowNav
        label={t("ride.workflow")}
        items={[
          { to: "/ride", label: t("ride.bookTab"), icon: <Route size={17} aria-hidden="true" />, end: true },
          { to: "/ride/activity", label: t("ride.activityTab"), icon: <Clock3 size={17} aria-hidden="true" /> }
        ]}
      />

      {mode === "book" && (accessIssue ? (
        <AccessNotice issue={accessIssue} />
      ) : (
        <Card as="form" className="ride-form" onSubmit={createRequest}>
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
          <Field label={`${t("ride.preferredTime")} (${CAMPUS_TIME_ZONE})`} type="datetime-local" value={preferredTime} onChange={(event) => setPreferredTime(event.target.value)} required />
          <Field
            label={t("ride.passengers")}
            type="number"
            min={1}
            max={8}
            value={passengerCount}
            onChange={(event) => setPassengerCount(Number(event.target.value))}
            required
          />
          <SelectField
            label={t("ride.genderPreference")}
            value={genderPreference}
            onChange={(event) => setGenderPreference(event.target.value)}
            options={[
              { label: t("ride.noPreference"), value: "none" },
              { label: t("ride.sameGender"), value: "same_gender" }
            ]}
          />
          <Button type="submit">
            {t("ride.createRequest")}
          </Button>
          <Toast message={formError} tone="error" />
          <Toast message={message} tone="success" />
        </Card>
      ))}

      {mode === "activity" && <Card className="records-panel">
        <div className="panel-title">
          <h2>{t("ride.myRequests")}</h2>
          <Button variant="icon" type="button" onClick={reload} aria-label={t("common.refreshRequests")}>
            <RefreshCw size={17} aria-hidden="true" />
          </Button>
        </div>
        {loading && <div className="skeleton-list" />}
        {error && <p className="inline-error">{error}</p>}
        {data?.map((request) => (
          <Card as="article" tone="strong" className="record-card" key={request.request_id}>
            <div>
              <strong>{request.origin} {t("common.routeJoiner")} {request.destination}</strong>
              <span>{formatDateTime(request.preferred_time, i18n.language === "en" ? "en-MY" : i18n.language)}</span>
            </div>
            <div className="record-meta">
              <StatusPill value={request.status} />
              <span>{request.distance_km ? `${request.distance_km}km` : t("ride.distancePending")}</span>
            </div>
            {!accessIssue && request.status === "pending" && (
              <div className="button-row">
                <Button variant="secondary" type="button" onClick={() => loadRecommendations(request.request_id)}>
                  {t("ride.findMatches")}
                </Button>
                <Button variant="ghost" type="button" onClick={() => api.cancelRideRequest(request.request_id).then(reload)}>
                  {t("common.cancel")}
                </Button>
              </div>
            )}
            {!accessIssue && matches[request.request_id]?.map((match) => (
              <MatchInsightCard
                key={match.match_id}
                match={match}
                label={t("ride.tripNumber", { id: match.trip_id })}
                actionLabel={t("common.confirm")}
                onAction={() => confirm(match.match_id)}
              />
            ))}
          </Card>
        ))}
      </Card>}

      {mode === "activity" && networkTrips.data?.map((trip) => (
        <TripNetworkPanel key={trip.trip_id} trip={trip} />
      ))}
    </div>
  );
}
