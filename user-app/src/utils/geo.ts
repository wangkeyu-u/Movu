import type { Point } from "../api/types";

export const TAYLORS_CENTER: Point = {
  label: "Taylor's University Lakeside Campus",
  latitude: 3.0646454,
  longitude: 101.6159384
};

export const SERVICE_RADIUS_KM = 30;

export const SERVICE_BOUNDS = {
  minLatitude: 2.7948,
  maxLatitude: 3.3345,
  minLongitude: 101.3461,
  maxLongitude: 101.8857
};

export const CAMPUS_STOPS: Point[] = [
  TAYLORS_CENTER,
  { label: "Sunway Pyramid", latitude: 3.0738, longitude: 101.607 },
  { label: "Sunway Medical Centre", latitude: 3.0678, longitude: 101.6039 },
  { label: "Subang Jaya LRT", latitude: 3.0845, longitude: 101.5881 },
  { label: "SS15 Courtyard", latitude: 3.0756, longitude: 101.5888 },
  { label: "Bandar Sunway BRT", latitude: 3.0719, longitude: 101.6115 },
  { label: "IOI Mall Puchong", latitude: 3.0462, longitude: 101.6182 },
  { label: "KL Sentral", latitude: 3.134, longitude: 101.6868 },
  { label: "Mid Valley Megamall", latitude: 3.1181, longitude: 101.6774 },
  { label: "One Utama", latitude: 3.1504, longitude: 101.6155 }
];

export function haversineDistanceKm(a: Point, b: Point): number {
  const radiusKm = 6371;
  const lat1 = toRadians(a.latitude);
  const lat2 = toRadians(b.latitude);
  const deltaLat = toRadians(b.latitude - a.latitude);
  const deltaLng = toRadians(b.longitude - a.longitude);
  const value =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;
  return roundKm(2 * radiusKm * Math.atan2(Math.sqrt(value), Math.sqrt(1 - value)));
}

export function isInsideServiceArea(point: Point): boolean {
  return haversineDistanceKm(TAYLORS_CENTER, point) <= SERVICE_RADIUS_KM;
}

export function roundKm(value: number): number {
  return Math.round(value * 10) / 10;
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

export function formatPoint(point?: Point | null, emptyLabel = "Choose on map"): string {
  if (!point) return emptyLabel;
  return `${point.label} · ${point.latitude.toFixed(4)}, ${point.longitude.toFixed(4)}`;
}

export function makePoint(label: string, latitude: number, longitude: number): Point {
  return { label, latitude, longitude };
}
