import { Button, Input, TabButton, Tabs } from "@movu/ui";
import { LocateFixed, MapPin, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Point } from "../api/types";
import {
  CAMPUS_STOPS,
  ROUTE_PRESETS,
  SERVICE_BOUNDS,
  SERVICE_RADIUS_KM,
  TAYLORS_CENTER,
  formatPoint,
  haversineDistanceKm,
  isInsideServiceArea,
  makePoint
} from "../utils/geo";

type Target = "origin" | "destination";

interface CampusMapPickerProps {
  origin: Point | null;
  destination: Point | null;
  onChange: (target: Target, point: Point) => void;
}

const ZOOM = 12;
const TILE_SIZE = 256;

interface Tile {
  x: number;
  y: number;
  left: number;
  top: number;
  url: string;
}

export function CampusMapPicker({ origin, destination, onChange }: CampusMapPickerProps) {
  const { t } = useTranslation();
  const mapRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ width: 360, height: 320 });
  const [target, setTarget] = useState<Target>("origin");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Point[]>(CAMPUS_STOPS);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({
        width: Math.max(280, entry.contentRect.width),
        height: Math.max(300, entry.contentRect.height)
      });
    });
    observer.observe(mapRef.current);
    return () => observer.disconnect();
  }, []);

  const centerPixel = useMemo(() => project(TAYLORS_CENTER.latitude, TAYLORS_CENTER.longitude, ZOOM), []);
  const tiles = useMemo(() => buildTiles(centerPixel, size.width, size.height), [centerPixel, size]);
  const serviceRadiusPx = useMemo(() => {
    const northEdge = project(TAYLORS_CENTER.latitude + SERVICE_RADIUS_KM / 111.32, TAYLORS_CENTER.longitude, ZOOM);
    return Math.abs(northEdge.y - centerPixel.y);
  }, [centerPixel]);

  async function searchPlaces(nextQuery: string) {
    setQuery(nextQuery);
    if (nextQuery.trim().length < 2) {
      setResults(CAMPUS_STOPS);
      return;
    }

    const localMatches = CAMPUS_STOPS.filter((stop) => stop.label.toLowerCase().includes(nextQuery.toLowerCase()));
    try {
      const params = new URLSearchParams({
        q: nextQuery,
        format: "jsonv2",
        limit: "6",
        countrycodes: "my",
        bounded: "1",
        viewbox: `${SERVICE_BOUNDS.minLongitude},${SERVICE_BOUNDS.maxLatitude},${SERVICE_BOUNDS.maxLongitude},${SERVICE_BOUNDS.minLatitude}`
      });
      const response = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`);
      const payload = (await response.json()) as Array<{ display_name: string; lat: string; lon: string }>;
      const remoteMatches = payload
        .map((item) => makePoint(item.display_name.split(",").slice(0, 2).join(","), Number(item.lat), Number(item.lon)))
        .filter(isInsideServiceArea);
      setResults([...localMatches, ...remoteMatches].slice(0, 8));
    } catch {
      setResults(localMatches);
    }
  }

  function choosePoint(point: Point) {
    if (!isInsideServiceArea(point)) {
      setMessage(t("map.outsideArea", { radius: SERVICE_RADIUS_KM }));
      return;
    }
    setMessage(null);
    onChange(target, point);
  }

  function choosePreset(originPoint: Point, destinationPoint: Point) {
    setMessage(null);
    onChange("origin", originPoint);
    onChange("destination", destinationPoint);
  }

  function chooseCurrentLocation() {
    if (!navigator.geolocation) {
      setMessage(t("common.locationUnavailable"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        choosePoint(
          makePoint(
            t("map.currentLocation"),
            roundCoordinate(position.coords.latitude),
            roundCoordinate(position.coords.longitude)
          )
        );
      },
      () => setMessage(t("map.readFailed")),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  function handleMapClick(event: React.PointerEvent<HTMLDivElement>) {
    if (!mapRef.current) return;
    const rect = mapRef.current.getBoundingClientRect();
    const point = unproject(
      centerPixel.x + (event.clientX - rect.left - rect.width / 2),
      centerPixel.y + (event.clientY - rect.top - rect.height / 2),
      ZOOM
    );
    choosePoint(makePoint(t("map.droppedPin"), roundCoordinate(point.latitude), roundCoordinate(point.longitude)));
  }

  function markerStyle(point: Point): React.CSSProperties {
    const projected = project(point.latitude, point.longitude, ZOOM);
    return {
      left: size.width / 2 + (projected.x - centerPixel.x),
      top: size.height / 2 + (projected.y - centerPixel.y)
    };
  }

  return (
    <section className="map-shell">
      <Tabs label={t("map.target")}>
        <TabButton active={target === "origin"} onClick={() => setTarget("origin")} type="button">
          {t("common.origin")}
        </TabButton>
        <TabButton active={target === "destination"} onClick={() => setTarget("destination")} type="button">
          {t("common.destination")}
        </TabButton>
      </Tabs>

      <div className="map-search">
        <Search size={17} aria-hidden="true" />
        <Input
          value={query}
          onChange={(event) => searchPlaces(event.target.value)}
          placeholder={t("map.searchPlaceholder")}
          aria-label={t("map.searchPlaces")}
        />
        {query && (
          <Button variant="icon" type="button" onClick={() => searchPlaces("")} aria-label={t("map.clearSearch")}>
            <X size={16} aria-hidden="true" />
          </Button>
        )}
      </div>

      <div className="map-results">
        {results.map((point) => (
          <Button key={`${point.label}-${point.latitude}-${point.longitude}`} className="map-result-button" variant="ghost" type="button" onClick={() => choosePoint(point)}>
            <MapPin size={15} aria-hidden="true" />
            <span>{point.label}</span>
            <small>{haversineDistanceKm(TAYLORS_CENTER, point)}km</small>
          </Button>
        ))}
      </div>

      <div className="route-presets" aria-label={t("map.routePresets")}>
        {ROUTE_PRESETS.map((preset) => (
          <Button key={preset.label} variant="ghost" type="button" onClick={() => choosePreset(preset.origin, preset.destination)}>
            <span>{preset.label}</span>
            <small>{haversineDistanceKm(preset.origin, preset.destination)}km</small>
          </Button>
        ))}
      </div>

      <div className="map-canvas" ref={mapRef} onPointerUp={handleMapClick}>
        {tiles.map((tile) => (
          <img
            alt=""
            aria-hidden="true"
            draggable="false"
            key={`${tile.x}-${tile.y}`}
            src={tile.url}
            style={{ left: tile.left, top: tile.top }}
          />
        ))}
        <div
          className="service-circle"
          style={{
            width: serviceRadiusPx * 2,
            height: serviceRadiusPx * 2,
            left: size.width / 2 - serviceRadiusPx,
            top: size.height / 2 - serviceRadiusPx
          }}
        />
        <div className="campus-dot" style={markerStyle(TAYLORS_CENTER)}>
          <span>Taylor's</span>
        </div>
        {origin && (
          <div className="pin origin" style={markerStyle(origin)}>
            O
          </div>
        )}
        {destination && (
          <div className="pin destination" style={markerStyle(destination)}>
            D
          </div>
        )}
        {origin && destination && <div className="route-line-preview" aria-hidden="true" />}
      </div>

      <div className="map-actions grab-route-panel">
        <Button variant="secondary" type="button" onClick={chooseCurrentLocation}>
          <LocateFixed size={17} aria-hidden="true" />
          {t("common.useCurrent")}
        </Button>
        <div>
          <strong>{target === "origin" ? t("common.origin") : t("common.destination")}</strong>
          <span>{formatPoint(target === "origin" ? origin : destination, t("map.chooseOnMap"))}</span>
        </div>
      </div>
      {message && <p className="inline-error">{message}</p>}
    </section>
  );
}

function buildTiles(centerPixel: { x: number; y: number }, width: number, height: number): Tile[] {
  const minX = Math.floor((centerPixel.x - width / 2) / TILE_SIZE);
  const maxX = Math.floor((centerPixel.x + width / 2) / TILE_SIZE);
  const minY = Math.floor((centerPixel.y - height / 2) / TILE_SIZE);
  const maxY = Math.floor((centerPixel.y + height / 2) / TILE_SIZE);
  const tiles: Tile[] = [];
  for (let x = minX; x <= maxX; x += 1) {
    for (let y = minY; y <= maxY; y += 1) {
      tiles.push({
        x,
        y,
        left: x * TILE_SIZE - (centerPixel.x - width / 2),
        top: y * TILE_SIZE - (centerPixel.y - height / 2),
        url: `https://tile.openstreetmap.org/${ZOOM}/${x}/${y}.png`
      });
    }
  }
  return tiles;
}

function project(latitude: number, longitude: number, zoom: number) {
  const scale = TILE_SIZE * 2 ** zoom;
  const x = ((longitude + 180) / 360) * scale;
  const sinLatitude = Math.sin((latitude * Math.PI) / 180);
  const y = (0.5 - Math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * Math.PI)) * scale;
  return { x, y };
}

function unproject(x: number, y: number, zoom: number) {
  const scale = TILE_SIZE * 2 ** zoom;
  const longitude = (x / scale) * 360 - 180;
  const latitude = (Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / scale))) * 180) / Math.PI;
  return { latitude, longitude };
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000000) / 1000000;
}
