import type {
  AuditLog,
  Match,
  Payment,
  RatingReport,
  RideRequest,
  SOSEvent,
  Trip,
  User,
  Vehicle
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";
const TOKEN_KEY = "movu_admin_token";

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

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  me: () => request<User>("/users/me"),
  users: () => request<User[]>("/users"),
  verifyUser: (id: number, verification_status: string) =>
    request<User>(`/users/${id}/verification`, {
      method: "PATCH",
      body: JSON.stringify({ verification_status })
    }),
  banUser: (id: number) => request<User>(`/users/${id}/ban`, { method: "PATCH" }),
  unbanUser: (id: number) => request<User>(`/users/${id}/unban`, { method: "PATCH" }),
  vehicles: () => request<Vehicle[]>("/vehicles"),
  verifyVehicle: (id: number, verification_status: string) =>
    request<Vehicle>(`/vehicles/${id}/verification`, {
      method: "PATCH",
      body: JSON.stringify({ verification_status })
    }),
  rideRequests: () => request<RideRequest[]>("/ride-requests"),
  trips: () => request<Trip[]>("/trips"),
  matches: () => request<Match[]>("/matches"),
  payments: () => request<Payment[]>("/payments"),
  sosEvents: () => request<SOSEvent[]>("/sos"),
  updateSos: (id: number, status: string) =>
    request<SOSEvent>(`/sos/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    }),
  reports: () => request<RatingReport[]>("/reports"),
  auditLogs: () => request<AuditLog[]>("/admin/audit-logs")
};
