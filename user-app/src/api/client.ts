import type { AuthResponse, LocationLog, Match, Notification, RatingReport, RideRequest, SOSEvent, Trip, TripMessage, TripNetwork, User, Vehicle } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";
const TOKEN_KEY = "movu_user_token";

export const authToken = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY)
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = authToken.get();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function locationSocketUrl(tripId: number): string | null {
  const token = authToken.get();
  if (!token) return null;
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/api\/?$/, "")}/ws/locations/${tripId}`;
  url.search = `token=${encodeURIComponent(token)}`;
  return url.toString();
}

export const api = {
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  register: (payload: Record<string, unknown>) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  verifyEmail: (token: string) =>
    request<User>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token })
    }),
  resendVerification: (email: string) =>
    request<{ message: string }>("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email })
    }),
  me: () => request<User>("/users/me"),
  rideRequests: () => request<RideRequest[]>("/ride-requests/me"),
  createRideRequest: (payload: Record<string, unknown>) =>
    request<RideRequest>("/ride-requests", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  cancelRideRequest: (id: number) => request<RideRequest>(`/ride-requests/${id}/cancel`, { method: "PATCH" }),
  trips: () => request<Trip[]>("/trips/me"),
  createTrip: (payload: Record<string, unknown>) =>
    request<Trip>("/trips", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateTripStatus: (id: number, status: string) =>
    request<Trip>(`/trips/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    }),
  vehicles: () => request<Vehicle[]>("/vehicles/me"),
  createVehicle: (payload: Record<string, unknown>) =>
    request<Vehicle>("/vehicles", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  requestRecommendations: (requestId: number) => request<Match[]>(`/matches/ride-requests/${requestId}/recommendations`),
  autoAssignRequest: (requestId: number) => request<Match>(`/matches/ride-requests/${requestId}/auto-assign`, { method: "POST" }),
  tripRecommendations: (tripId: number) => request<Match[]>(`/matches/trips/${tripId}/recommendations`),
  confirmMatch: (matchId: number) => request<Match>(`/matches/${matchId}/confirm`, { method: "POST" }),
  rejectMatch: (matchId: number) => request<Match>(`/matches/${matchId}/reject`, { method: "POST" }),
  sendLocation: (payload: Record<string, unknown>) =>
    request<unknown>("/locations", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  latestTripLocation: (tripId: number) => request<LocationLog>(`/locations/trips/${tripId}/latest`),
  networkTrips: () => request<TripNetwork[]>("/network/me/trips"),
  tripMessages: (tripId: number) => request<TripMessage[]>(`/network/trips/${tripId}/messages`),
  sendTripMessage: (tripId: number, body: string) =>
    request<TripMessage>(`/network/trips/${tripId}/messages`, {
      method: "POST",
      body: JSON.stringify({ body })
    }),
  currentSafetyTrip: () => request<Trip>("/sos/current-trip"),
  triggerSos: (payload: Record<string, unknown>) =>
    request<SOSEvent>("/sos", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  notifications: () => request<Notification[]>("/notifications/me"),
  unreadNotifications: () => request<{ unread_count: number }>("/notifications/me/unread-count"),
  markNotificationRead: (notificationId: number) =>
    request<Notification>(`/notifications/${notificationId}/read`, { method: "PATCH" }),
  markAllNotificationsRead: () =>
    request<{ unread_count: number }>("/notifications/me/read-all", { method: "PATCH" }),
  reports: () => request<RatingReport[]>("/reports/me?direction=given"),
  createRating: (payload: Record<string, unknown>) =>
    request<RatingReport>("/reports/ratings", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  createReport: (payload: Record<string, unknown>) =>
    request<RatingReport>("/reports", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};
