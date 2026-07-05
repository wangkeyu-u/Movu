# MovU Carpooling

MovU is a campus carpooling platform for Taylor's University students and staff. It supports email-verified campus users, rider-driver matching, automatic assignment, verified vehicle display, multi-passenger trip networks, route-distance calculation, WebSocket live location tracking, SOS safety alerts, ratings, reports, audit logs, and an admin dashboard.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, MySQL, JWT, SMTP email, OSRM routing, WebSocket
- Admin dashboard: React, TypeScript, Vite, react-i18next
- User app: React, TypeScript, Vite, PWA, OpenStreetMap tiles, Nominatim search
- Shared UI: `packages/ui` with reusable MovU primitives
- Testing: pytest with isolated SQLite, Playwright E2E against Docker backend
- Deployment: Docker Compose

## UI System

All frontend surfaces must reuse `packages/ui/src/components` for base UI primitives. Do not recreate Button, Card, Input, Alert, Badge, Dialog, Tabs, Sheet, Switch, Select, or equivalent components inside app folders.

Run the guard:

```bash
npm run ui:check
```

See `packages/ui/README.md` and `CONTRIBUTING.md` for the component rules and shadcn onboarding notes.

## Backend

```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --reload --app-dir backend
```

Health check:

```text
http://127.0.0.1:8000/health
```

Run tests:

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
```

Run end-to-end flow tests:

```bash
npm run e2e:install
npm run e2e
```

The E2E suite starts or reuses Docker backend, resets seed data, runs current-source Vite dev servers on `127.0.0.1:6173` and `127.0.0.1:6174`, and verifies registration, email verification via local backend email logs, pending approval gating, admin approval, vehicle approval, matching, location, SOS, rating, and audit logs.

Seed local development data:

```bash
PYTHONPATH=backend .venv/bin/python -m app.db.seed
```

Sample password for all seeded accounts:

```text
Password123
```

Sample accounts:

- Admin: `admin@taylors.edu.my`
- Rider: `aina@sd.taylors.edu.my`
- Rider: `jason@sd.taylors.edu.my`
- Driver: `daniel@sd.taylors.edu.my`
- Driver: `mei@sd.taylors.edu.my`

## Admin Dashboard

```bash
cd admin-dashboard
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The dashboard includes separate pages for overview, users, vehicles, ride requests, trips, matches, payments, SOS events, ratings/reports, and audit logs. It supports English, Simplified Chinese, and Bahasa Malaysia.

## User App

```bash
cd user-app
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5174
```

The user app is mobile-first and PWA-ready. It includes email login/registration, rider requests, driver vehicle/trip flows, OpenStreetMap-based place search, 30km Taylor's University service-area validation, live location sharing, SOS, account trust status, and English/Simplified Chinese/Bahasa Malaysia language switching. Payment actions are disabled until an approved payment provider is configured.

## Docker

```bash
docker compose up --build
```

Local Docker verification has been run with Colima-backed Docker:

```bash
docker compose config
docker compose build
docker compose up -d
```

Then seed the database:

```bash
docker compose exec backend python -m app.db.seed
```

Services:

- Backend API: `http://localhost:8000`
- Admin dashboard: `http://localhost:5173`
- User app: `http://localhost:5174`
- MySQL: `localhost:3306`

## Production Notes

Production mode is stricter than local development:

- `ENVIRONMENT=production` refuses weak JWT secrets.
- Production refuses SQLite.
- Production requires SMTP settings for email verification.
- Production requires `OSRM_BASE_URL`; ride requests and trips must include coordinates within 30km of Taylor's University Lakeside Campus.
- Rider and driver core actions require both verified email and admin-approved account status.
- Local seed/reset is blocked in production.
- Simulated payments are blocked in production. Payment collection remains disabled until an approved provider is configured.
- Backend containers run `alembic upgrade head` before serving traffic.
- Match confirmation uses database row-level locking so concurrent riders cannot reserve the same seat twice on databases that support `SELECT ... FOR UPDATE`.
- Trip network responses include the driver, approved vehicle, confirmed riders, seats, chat, and live location hooks.
- Ride and trip schedule inputs are interpreted as Taylor's campus time (`Asia/Kuala_Lumpur`) and stored with timezone metadata plus UTC timestamps.
- Security-sensitive admin actions are written to audit logs.
- Basic API rate limiting is enabled; use Redis-backed rate limiting before running multiple backend replicas.

Use `.env.production.example`, `backend/.env.production.example`, and `docker-compose.prod.yml` as the production starting point. Configure `PUBLIC_API_BASE_URL` during frontend image builds, plus a real SMTP provider and a production-grade routing/search endpoint before accepting real users. Production mode will not accept simulated payment calls.

See `DEPLOYMENT.md` for the production Docker Compose checklist, required environment variables, health checks, and rollback notes.

## API Overview

- `POST /api/auth/register`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification`
- `POST /api/auth/login`
- `GET /api/users`
- `PATCH /api/users/{user_id}/verification`
- `PATCH /api/users/{user_id}/ban`
- `POST /api/vehicles`
- `PATCH /api/vehicles/{vehicle_id}/verification`
- `POST /api/ride-requests`
- `POST /api/trips`
- `GET /api/matches/ride-requests/{request_id}/recommendations`
- `POST /api/matches/ride-requests/{request_id}/auto-assign`
- `POST /api/matches/{match_id}/confirm`
- `GET /api/network/me/trips`
- `GET /api/network/trips/{trip_id}/messages`
- `POST /api/network/trips/{trip_id}/messages`
- `POST /api/locations`
- `WS /ws/locations/{trip_id}`
- `POST /api/sos`
- `WS /ws/admin/sos`
- `POST /api/reports/ratings`
- `POST /api/reports`
- `GET /api/admin/audit-logs`

Local-only payment test endpoint:

- `POST /api/payments/matches/{match_id}/simulate` is available outside production for local development and automated tests only.

## Matching Algorithm

MovU uses a route-insertion matching algorithm inspired by real ride-pooling systems. Instead of only comparing pickup and destination distance, the system estimates whether a passenger can be inserted into the driver's existing route with acceptable detour. The algorithm checks hard constraints, estimates driver detour, evaluates route alignment, passenger convenience, driver acceptance probability, supply efficiency, and trust/safety factors. Only matches above the minimum score are returned.

The algorithm borrows public ride-pooling design principles: prefer similar route direction, protect drivers from excessive detours, place pickup/dropoff near the driver's route where possible, avoid recommending rides drivers are unlikely to accept, and avoid consuming scarce supply with low-quality matches.

Hard constraints include request/trip status, seats, driver/passenger separation, a 30-minute departure window, same-gender preference, Taylor's 30km service area checks when coordinates are present, opposite-direction rejection, maximum driver detour, and maximum passenger walking distance to the driver route. When both sides have route coordinates, MovU uses the coordinate algorithm. Records with incomplete coordinates fall back to text matching, but receive lower confidence and should not outrank good coordinate-based matches.

Score weighting is configurable in `backend/app/core/config.py`:

- Route alignment: 25%
- Driver detour: 20%
- Passenger convenience: 20%
- Time fit: 15%
- Driver acceptance: 10%
- Supply efficiency: 5%
- Trust and safety: 5%

The API returns the top five recommendations ordered by `match_score`. Each recommendation also includes `score_breakdown` and explainable `reasons`.

## Operational Flow

1. Admin logs in and approves users or vehicles.
2. Rider creates a ride request.
3. Approved driver creates a trip.
4. Rider or driver views match recommendations.
5. A match is confirmed and seats are reduced.
6. Driver sends live location during an ongoing trip.
7. Rider triggers SOS and admin receives an alert.
8. Completed trip participants submit ratings or reports.

## Chinese Design Docs

Chinese architecture, runtime, algorithm, database relationship, high-concurrency, use case, and sequence guidance lives in:

- `docs/zh_design_and_release.md`
- `docs/DIAGRAM_GUIDE.md`
