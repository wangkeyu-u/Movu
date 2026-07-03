export type Role = "rider" | "driver" | "admin";
export type VerificationStatus = "pending" | "approved" | "rejected";
export type TripStatus = "posted" | "matched" | "ongoing" | "completed" | "cancelled" | "full";
export type RequestStatus = "pending" | "matched" | "cancelled" | "completed";
export type MatchStatus = "recommended" | "confirmed" | "rejected" | "cancelled" | "completed";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";
export type SOSStatus = "new" | "reviewing" | "resolved" | "false_alarm";

export interface User {
  user_id: number;
  name: string;
  email: string;
  email_verified: boolean;
  student_id?: string | null;
  role: Role;
  gender: string;
  rating: number;
  verification_status: VerificationStatus;
  is_banned: boolean;
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
  available_seats: number;
  total_seats: number;
  status: TripStatus;
  created_at: string;
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

export interface Payment {
  payment_id: number;
  match_id: number;
  payer_id: number;
  amount: number;
  payment_status: PaymentStatus;
  payment_method: string;
  created_at: string;
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

export interface AuditLog {
  audit_id: number;
  actor_user_id?: number | null;
  action: string;
  entity_type: string;
  entity_id: string;
  metadata_json?: string | null;
  ip_address?: string | null;
  created_at: string;
}
