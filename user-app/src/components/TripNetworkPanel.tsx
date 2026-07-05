import { Button, Card, Input } from "@movu/ui";
import { CarFront, MapPinned, MessageCircle, Navigation, RefreshCw, Send, Signal, Square, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, locationSocketUrl } from "../api/client";
import type { LocationLog, TripNetwork, TripMessage } from "../api/types";
import { useAuth } from "../routes/AuthProvider";
import { formatDateTime } from "../utils/format";

interface TripNetworkPanelProps {
  trip: TripNetwork;
}

export function TripNetworkPanel({ trip }: TripNetworkPanelProps) {
  const { user } = useAuth();
  const { i18n, t } = useTranslation();
  const socketRef = useRef<WebSocket | null>(null);
  const watchIdRef = useRef<number | null>(null);
  const [messages, setMessages] = useState<TripMessage[]>([]);
  const [latestLocation, setLatestLocation] = useState<LocationLog | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);
  const [liveSharing, setLiveSharing] = useState(false);

  async function reloadNetwork() {
    setError(null);
    try {
      const [nextMessages, location] = await Promise.all([
        api.tripMessages(trip.trip_id),
        api.latestTripLocation(trip.trip_id).catch(() => null)
      ]);
      setMessages(nextMessages);
      setLatestLocation(location);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.somethingWrong"));
    }
  }

  async function sendMessage(event: React.FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;
    setDraft("");
    try {
      const message = await api.sendTripMessage(trip.trip_id, body);
      setMessages((prev) => [...prev, message]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.somethingWrong"));
    }
  }

  async function publishLocation(position: GeolocationPosition) {
    const payload = {
      trip_id: trip.trip_id,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude
    };
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ latitude: payload.latitude, longitude: payload.longitude }));
      return;
    }
    await api.sendLocation(payload);
  }

  async function shareDriverLocation() {
    setError(null);
    setLocationStatus(null);
    if (!navigator.geolocation) {
      setError(t("map.readFailed"));
      return;
    }
    setLocating(true);
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 9000 });
      });
      await publishLocation(position);
      setLocationStatus(t("network.locationShared"));
      await reloadNetwork();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("map.readFailed"));
    } finally {
      setLocating(false);
    }
  }

  function startLiveSharing() {
    setError(null);
    setLocationStatus(null);
    if (!navigator.geolocation) {
      setError(t("map.readFailed"));
      return;
    }
    if (watchIdRef.current !== null) return;
    setLiveSharing(true);
    setLocationStatus(t("network.liveSharingOn"));
    watchIdRef.current = navigator.geolocation.watchPosition(
      async (position) => {
        try {
          await publishLocation(position);
          setLatestLocation({
            log_id: Date.now(),
            trip_id: trip.trip_id,
            user_id: user?.user_id ?? 0,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            timestamp: new Date().toISOString()
          });
        } catch (err) {
          setError(err instanceof Error ? err.message : t("map.readFailed"));
        }
      },
      (geoError) => {
        setError(geoError.message || t("map.readFailed"));
        stopLiveSharing();
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
    );
  }

  function stopLiveSharing() {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setLiveSharing(false);
    setLocationStatus(null);
  }

  useEffect(() => {
    reloadNetwork();
    const interval = window.setInterval(reloadNetwork, 8000);
    return () => window.clearInterval(interval);
  }, [trip.trip_id]);

  useEffect(() => {
    const url = locationSocketUrl(trip.trip_id);
    if (!url) return undefined;
    const socket = new WebSocket(url);
    socketRef.current = socket;
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as Omit<LocationLog, "log_id">;
        setLatestLocation({ log_id: Date.now(), ...message });
      } catch {
        setError(t("common.somethingWrong"));
      }
    };
    return () => {
      if (socketRef.current === socket) socketRef.current = null;
      socket.close();
    };
  }, [trip.trip_id, t]);

  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, []);

  return (
    <Card className="network-panel">
      <div className="panel-title">
        <div>
          <h2>{t("network.title")}</h2>
          <span>{trip.origin} {t("common.routeJoiner")} {trip.destination}</span>
        </div>
        <Button variant="icon" type="button" onClick={reloadNetwork} aria-label={t("common.refreshTrips")}>
          <RefreshCw size={16} aria-hidden="true" />
        </Button>
      </div>

      <div className="network-roster">
        <div className="network-roster-card">
          <CarFront size={18} aria-hidden="true" />
          <div>
            <strong>{trip.driver.name}</strong>
            <span>{trip.vehicle ? `${trip.vehicle.vehicle_model} · ${trip.vehicle.plate_number}` : t("network.noVehicle")}</span>
            <small>{trip.available_seats}/{trip.total_seats} {t("network.seatsAvailable")}</small>
          </div>
        </div>
        <div className="network-roster-card">
          <Users size={18} aria-hidden="true" />
          <div>
            <strong>{t("network.passengers")}</strong>
            <span>
              {trip.riders.length
                ? trip.riders.map((rider) => `${rider.name} (${rider.passenger_count})`).join(", ")
                : t("network.noPassengers")}
            </span>
          </div>
        </div>
      </div>

      <div className="driver-location-card">
        <MapPinned size={18} aria-hidden="true" />
        <div>
          <strong>{t("network.driverLocation")}</strong>
          <span>
            {latestLocation
              ? `${latestLocation.latitude.toFixed(5)}, ${latestLocation.longitude.toFixed(5)} · ${formatDateTime(latestLocation.timestamp, i18n.language === "en" ? "en-MY" : i18n.language)}`
              : t("network.locationPending")}
          </span>
        </div>
        {user?.role === "driver" && trip.status === "ongoing" && (
          <div className="driver-location-actions">
            <Button variant="secondary" type="button" onClick={shareDriverLocation} disabled={locating || liveSharing}>
              <Navigation size={16} aria-hidden="true" />
              {locating ? t("network.locating") : t("network.shareLocation")}
            </Button>
            <Button variant={liveSharing ? "danger" : "secondary"} type="button" onClick={liveSharing ? stopLiveSharing : startLiveSharing}>
              {liveSharing ? <Square size={16} aria-hidden="true" /> : <Signal size={16} aria-hidden="true" />}
              {liveSharing ? t("network.stopLiveSharing") : t("network.startLiveSharing")}
            </Button>
          </div>
        )}
      </div>

      <div className="message-list" aria-label={t("network.messages")}>
        {messages.map((message) => (
          <div className="message-bubble" key={message.message_id}>
            <span>{message.sender_name} · {t(`roles.${message.sender_role}`, { defaultValue: message.sender_role })}</span>
            <p>{message.body}</p>
          </div>
        ))}
        {!messages.length && (
          <div className="empty-copy">
            <MessageCircle size={17} aria-hidden="true" />
            {t("network.emptyMessages")}
          </div>
        )}
      </div>

      <form className="message-form" onSubmit={sendMessage}>
        <Input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("network.messagePlaceholder")} />
        <Button variant="secondary" type="submit" aria-label={t("network.sendMessage")}>
          <Send size={16} aria-hidden="true" />
        </Button>
      </form>
      {locationStatus && <p className="inline-success">{locationStatus}</p>}
      {error && <p className="inline-error">{error}</p>}
    </Card>
  );
}
