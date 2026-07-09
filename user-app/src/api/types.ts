export type Role = "rider" | "driver" | "admin";
export type VerificationStatus = "pending" | "approved" | "rejected";
export type TripStatus = "posted" | "matched" | "ongoing" | "completed" | "cancelled" | "full";
export type RequestStatus = "pending" | "matched" | "cancelled" | "completed";
export type MatchStatus = "recommended" | "confirmed" | "rejected" | "cancelled" | "completed";
export type SOSStatus = "new" | "reviewing" | "resolved" | "false_alarm";

export interface User {
  user_id: number;
  name: string;
  email: string;
  student_id?: string | null;
  role: Role;
  gender: string;
  rating: number;
  verification_status: VerificationStatus;
  email_verified: boolean;
  is_banned: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RideRequest {
  request_id: number;
  rider_id: number;
  origin: string;
  destination: string;
  origin_latitude?: number | null;
  origin_longitude?: number | null;
  destination_latitude?: number | null;
  destination_longitude?: number | null;
  preferred_time: string;
  preferred_time_timezone: string;
  passenger_count: number;
  gender_preference: string;
  distance_km?: number | null;
  status: RequestStatus;
  created_at: string;
}

export interface Trip {
  trip_id: number;
  driver_id: number;
  origin: string;
  destination: string;
  origin_latitude?: number | null;
  origin_longitude?: number | null;
  destination_latitude?: number | null;
  destination_longitude?: number | null;
  departure_time: string;
  departure_time_timezone: string;
  available_seats: number;
  total_seats: number;
  status: TripStatus;
  created_at: string;
}

export interface Vehicle {
  vehicle_id: number;
  driver_id: number;
  plate_number: string;
  vehicle_model: string;
  seat_count: number;
  verification_status: VerificationStatus;
  created_at: string;
}

export interface NetworkUser {
  user_id: number;
  name: string;
  role: Role;
  rating: number;
}

export interface NetworkVehicle {
  vehicle_id: number;
  plate_number: string;
  vehicle_model: string;
  seat_count: number;
  verification_status: VerificationStatus;
}

export interface NetworkRider {
  user_id: number;
  name: string;
  rating: number;
  passenger_count: number;
  pickup: string;
  dropoff: string;
}

export interface TripNetwork extends Trip {
  driver: NetworkUser;
  vehicle?: NetworkVehicle | null;
  riders: NetworkRider[];
}

export interface Match {
  match_id: number;
  trip_id: number;
  request_id: number;
  rider_id: number;
  match_score: number;
  score_breakdown: Record<string, number>;
  reasons: string[];
  status: MatchStatus;
  created_at: string;
}

export interface TripMessage {
  message_id: number;
  trip_id: number;
  sender_id: number;
  sender_name: string;
  sender_role: Role;
  body: string;
  created_at: string;
}

export interface LocationLog {
  log_id: number;
  trip_id: number;
  user_id: number;
  latitude: number;
  longitude: number;
  timestamp: string;
}

export interface SOSEvent {
  sos_id: number;
  user_id: number;
  trip_id: number;
  latitude: number;
  longitude: number;
  status: SOSStatus;
  triggered_time: string;
  resolved_time?: string | null;
  assigned_admin_id?: number | null;
  response_note?: string | null;
  status_updated_at?: string | null;
}

export interface Notification {
  notification_id: number;
  user_id: number;
  title: string;
  body: string;
  category: string;
  entity_type?: string | null;
  entity_id?: string | null;
  read_at?: string | null;
  created_at: string;
}

export interface RatingReport {
  record_id: number;
  from_user_id: number;
  to_user_id: number;
  trip_id: number;
  score?: number | null;
  report_type?: string | null;
  comment?: string | null;
  created_at: string;
}

export interface Point {
  label: string;
  latitude: number;
  longitude: number;
}
