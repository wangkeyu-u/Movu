# MovU architecture

## Components

| Path | Responsibility |
| --- | --- |
| `user-app/` | Rider and driver flows, campus map, trip network |
| `admin-dashboard/` | Account/vehicle approval, SOS, reports and audit |
| `packages/ui/` | Shared presentation primitives |
| `backend/app/api/` | Authenticated HTTP and WebSocket routes |
| `backend/app/services/` | Matching, routing, notification and location behavior |
| `backend/app/models/` | Users, vehicles, requests, trips and related records |

The frontends call the backend through their API clients; they do not operate on the database. MySQL stores operational state. SMTP handles verification email and OSRM supplies routing information when configured.

## Trip and match flow

1. A verified, approved rider creates a ride request.
2. An approved driver posts a trip with an approved vehicle.
3. `services/matching.py` evaluates candidates and returns the top five with a score breakdown and reasons.
4. `api/matches.py` confirms a match in a transaction and updates seats and request state. It uses row locks on databases that support `SELECT ... FOR UPDATE`.
5. `api/network.py` aggregates the driver, vehicle, confirmed riders and messages for the trip panel.

Seat correctness under production concurrency depends on the configured database and transaction behavior; isolated SQLite tests do not establish MySQL load capacity.

## Matching

Hard constraints cover request/trip state, seats, departure time, gender preference and service area. Coordinate candidates also check direction, route order, detour and pickup/dropoff offsets. The route-insertion estimate uses geographic geometry; it is not a city-scale dispatch optimizer or a learned acceptance predictor.

The configurable score combines route alignment, driver detour, passenger convenience, time fit, driver acceptance estimate, supply efficiency and trust. Incomplete coordinate records use a lower-confidence text fallback outside the stricter production input gate. Constants and weights live in `backend/app/core/config.py`.

## Location and access

`services/location.py` validates trip access before recording coordinates. Drivers can publish location for their own ongoing trip; confirmed riders can read the corresponding trip. `services/realtime.py` holds WebSocket subscribers in process memory. Multiple backend processes need a shared broadcast mechanism before clients on different processes receive the same updates.

Location and trip chat access are enforced by backend routes. SOS creates a stored event and sends the admin alert through the realtime manager; reliable external emergency dispatch is outside this implementation.

## Time and operational boundaries

Schedule entry uses campus time, `Asia/Kuala_Lumpur`; timestamps are converted to UTC and stored with timezone metadata. The UI formats them back in campus time.

Production guards reject weak secrets and SQLite, require SMTP/routing configuration, and block sample-data reset and simulated payments. These checks do not replace infrastructure setup, backups, real provider validation or concurrency tests. See [deployment](../DEPLOYMENT.md) and [requirement coverage](../REQUIREMENTS_TRACE.md) for commands and implementation locations.
