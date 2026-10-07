# MovU — Campus carpooling

Taylor's University campus carpooling prototype: rider requests, verified drivers and vehicles, route matching, trip chat, live location, SOS alerts and administration. The React user app and admin dashboard support English, Simplified Chinese and Bahasa Malaysia.

![MovU](docs/assets/readme-hero.png)

## Quick start

Install Docker Desktop, OrbStack or Colima, then run from a cloned checkout:

```bash
bash scripts/bootstrap.sh
```

The script builds and starts MySQL, FastAPI and both frontends, waits for backend health, and seeds local sample accounts.

| Service | Local URL |
| --- | --- |
| User app | http://localhost:5174 |
| Admin dashboard | http://localhost:5173 |
| API | http://localhost:8000 |

Sample accounts use `Password123`: `admin@taylors.edu.my`, `aina@sd.taylors.edu.my` (rider), and `daniel@sd.taylors.edu.my` (driver).

## Repository

```text
backend/           FastAPI, SQLAlchemy models, Alembic migrations and tests
user-app/          React + TypeScript rider/driver PWA
admin-dashboard/   React + TypeScript administration
packages/ui/       Shared UI primitives
scripts/           Bootstrap, development and UI checks
e2e/               Playwright flow tests
docs/              Architecture and product images
```

## Development and tests

Node.js 22+ is needed for the workspace scripts. Install the frontend dependencies with `npm run setup`. For a backend development environment, install `backend/requirements.txt` in `.venv`.

```bash
npm run dev
npm run logs
npm run stop

PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm run ui:check
npm run e2e:install
npm run e2e
```

The backend tests use isolated SQLite. E2E starts/reuses Docker, resets local seed data, and runs the frontends on ports 6173/6174. It covers registration, approval, matching, location, SOS, reports and audit logs. These commands do not establish production load capacity.

## Design and deployment

- [Architecture](docs/architecture.md): matching, permissions, state and realtime boundaries.
- [Deployment](DEPLOYMENT.md): production environment, migrations, health checks and rollback.
- [Requirement coverage](REQUIREMENTS_TRACE.md): implementation and test locations.
- [Contributing](CONTRIBUTING.md) and [shared UI](packages/ui/README.md): component rules.

Production configuration requires MySQL, strong JWT secrets, SMTP and routing configuration. Coordinates are required within the 30 km campus service area. Payment collection remains disabled until an approved provider is integrated; simulated payments and seed/reset are local/test-only. A deployment still needs configured infrastructure and operational verification.
