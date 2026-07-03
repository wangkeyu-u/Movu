# MovU Requirements Trace

This document maps the original capstone requirements to the current MovU implementation. It is intended for project review, testing, and production-readiness checks.

## Scope Position

MovU is implemented as a production-ready campus carpooling platform for Taylor's University. The current build includes backend APIs, admin dashboard, user web app/PWA, Docker deployment files, production configuration guards, and test coverage. Payment collection is disabled until an approved provider is configured; simulated payment remains local/test-only and is blocked in production.

## Requirement Coverage

| # | Requirement | Status | Main Implementation | Verification |
|---|---|---|---|---|
| 1 | Authentication and user management | Done | `backend/app/api/auth.py`, `backend/app/api/users.py`, `backend/app/core/security.py`, `backend/app/services/email_verification.py` | `backend/tests/test_auth.py`, `backend/tests/test_vehicles.py` |
| 2 | Taylor's email restriction | Done | `backend/app/schemas/auth.py`, `backend/app/core/config.py` | `backend/tests/test_auth.py` |
| 3 | JWT auth and password hashing | Done | `backend/app/core/security.py`, `backend/app/core/dependencies.py` | `backend/tests/test_auth.py` |
| 4 | Admin user verify, ban, unban | Done | `backend/app/api/users.py`, `backend/app/core/dependencies.py`, `admin-dashboard/src/pages/UsersPage.tsx` | `backend/tests/test_auth.py`, `backend/tests/test_ride_requests_trips.py`, `backend/tests/test_vehicles.py`, frontend build |
| 5 | Vehicle registration and admin verification | Done | `backend/app/api/vehicles.py`, `backend/app/services/vehicles.py`, `admin-dashboard/src/pages/VehiclesPage.tsx` | `backend/tests/test_vehicles.py` |
| 6 | Only approved drivers can create trips | Done | `backend/app/api/trips.py`, `backend/app/services/vehicles.py` | `backend/tests/test_ride_requests_trips.py` |
| 7 | Rider request flow | Done | `backend/app/api/ride_requests.py`, `user-app/src/pages/RidePage.tsx` | `backend/tests/test_ride_requests_trips.py`, user app build |
| 8 | Driver trip flow | Done | `backend/app/api/trips.py`, `user-app/src/pages/DrivePage.tsx` | `backend/tests/test_ride_requests_trips.py`, user app build |
| 9 | Production-style ride-pooling matching algorithm | Done | `backend/app/services/matching.py`, `backend/app/api/matches.py`; hard constraints cover seats, time window, request/trip state, gender preference, service area, route direction, driver detour, and passenger walk distance; score combines route alignment, driver detour, passenger convenience, time fit, driver acceptance, supply efficiency, and trust/safety | `backend/tests/test_matching.py` |
| 10 | Matching top 5 ordered by score | Done | `backend/app/services/matching.py`; coordinate route insertion is preferred when available, incomplete-coordinate text fallback is lower confidence, and responses include score breakdowns plus explainable reasons | `backend/tests/test_matching.py` |
| 11 | Fare calculation and payment records | Done | `backend/app/services/payments.py`, `backend/app/api/payments.py` | `backend/tests/test_payments.py` |
| 12 | Local payment test flow | Production guarded | Local/test-only endpoint exists; production blocks simulation and payment collection stays disabled until provider configuration is added | `backend/tests/test_payments.py` |
| 13 | Real-time location tracking by WebSocket | Done | `backend/app/api/location.py`, `backend/app/services/location.py`, `backend/app/services/realtime.py` | `backend/tests/test_locations.py` |
| 14 | SOS safety feature and admin alerts | Done | `backend/app/api/sos.py`, `backend/app/models/sos_event.py`, `admin-dashboard/src/pages/SOSEventsPage.tsx` | `backend/tests/test_sos.py` |
| 15 | Ratings and reports | Done | `backend/app/api/reports.py`, `backend/app/services/ratings.py`, `admin-dashboard/src/pages/ReportsPage.tsx` | `backend/tests/test_reports.py` |
| 16 | Admin dashboard pages | Done | `admin-dashboard/src/pages/*`, `admin-dashboard/src/routes/AppLayout.tsx` | `cd admin-dashboard && npm run build` |
| 17 | Admin multilingual support | Done | `admin-dashboard/src/i18n/index.ts`, `admin-dashboard/src/i18n/locales/*.json`, `admin-dashboard/src/components/LanguageSwitcher.tsx` | JSON parse check, admin build |
| 18 | SQLAlchemy database models | Done | `backend/app/models/*` | Alembic migration check, backend tests |
| 19 | Clean API route structure | Done | `backend/app/api/auth.py`, `users.py`, `vehicles.py`, `ride_requests.py`, `trips.py`, `matches.py`, `payments.py`, `location.py`, `sos.py`, `reports.py`, `admin.py` | Backend import/tests |
| 20 | Clean project structure | Done | `backend/`, `admin-dashboard/`, `user-app/`, `packages/ui/`, Docker files | File tree, builds |
| 21 | Seed data | Done | `backend/app/db/seed.py` | Seed smoke with record counts |
| 22 | Simple tests | Done | `backend/tests/*`, `e2e/movu-flow.spec.ts` | `PYTHONPATH=backend .venv/bin/pytest backend/tests -q`, `npm run e2e` |
| 23 | README | Done | `README.md`, `PRODUCT.md` | Manual review |
| 24 | Docker deployment | Done | `docker-compose.yml`, `docker-compose.prod.yml`, `backend/Dockerfile`, frontend Dockerfiles, `DEPLOYMENT.md` | `docker compose config`, `docker compose build`, `docker compose up -d`, health checks |
| 25 | Taylor's University 30km operating area | Done | `backend/app/core/config.py`, `backend/app/services/maps.py`, `user-app/src/components/CampusMapPicker.tsx`, `user-app/src/utils/geo.ts` | Backend tests and user app build |
| 26 | Shared UI component rule | Done | `packages/ui/src/components/*`, `scripts/check-ui-usage.mjs`, `CONTRIBUTING.md` | `npm run ui:check` |
| 27 | User app multilingual support | Done | `user-app/src/i18n/index.ts`, `user-app/src/i18n/locales/*.json`, `user-app/src/components/LanguageSwitcher.tsx` | User app build, locale JSON parse |
| 28 | Reproducible frontend installs | Done | `admin-dashboard/package-lock.json`, `user-app/package-lock.json`, frontend Dockerfiles, CI | `npm ci && npm run build` in both apps |

## Production Hardening Already Included

- Production refuses SQLite.
- Production requires a strong JWT secret.
- Production requires SMTP configuration for email verification.
- Production requires OSRM routing configuration.
- Production blocks seed/reset behavior.
- Production blocks simulated payment completion.
- Ride requests and trips require coordinates in production.
- Taylor's University service area is constrained to 30km.
- Rider and driver core actions require email verification plus admin-approved account status.
- Admin-sensitive actions create audit logs.
- Basic API rate limiting is enabled.

## Current Known Gaps

| Gap | Impact | Next Action |
|---|---|---|
| Payment provider configuration | Real money collection/refunds remain disabled | Configure and certify an approved provider before enabling payment collection |
| Rate limiter is in-memory | Fine for one backend instance; not enough for multiple replicas | Replace with Redis-backed rate limiting before horizontal scaling |

## Repeatable Verification Commands

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm run ui:check
npm run e2e
cd user-app && npm run build
cd ../admin-dashboard && npm run build
```

Optional migration check:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./migration_check.db PYTHONPATH=. ../.venv/bin/alembic -c alembic.ini upgrade head
DATABASE_URL=sqlite+pysqlite:///./migration_check.db PYTHONPATH=. ../.venv/bin/alembic -c alembic.ini downgrade base
```

Optional seed check:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./seed_check.db PYTHONPATH=. ../.venv/bin/python -m app.db.seed
```
