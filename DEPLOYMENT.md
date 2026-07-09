# MovU Deployment Guide

This guide describes how to run MovU as a real deployable system with Docker Compose. Local Docker verification was performed with Docker CLI, Docker Compose, Buildx, and Colima.

## Services

- `mysql`: MySQL 8.4 database
- `redis`: shared rate limiting state
- `backend`: FastAPI API, Alembic migrations, WebSocket endpoints
- `admin-dashboard`: React admin dashboard served by Nginx
- `user-app`: React PWA served by Nginx

## Development Compose

```bash
docker compose up --build
```

Open:

- Backend health: `http://localhost:8000/health`
- Admin dashboard: `http://localhost:5173`
- User app: `http://localhost:5174`

Seed local development data only after the backend is healthy:

```bash
docker compose exec backend python -m app.db.seed
```

Seed data is blocked in production.

## Production Compose

1. Copy the environment template.

```bash
cp .env.production.example .env.production
```

2. Fill every secret and public URL in `.env.production`.

Required values:

- `MOVU_DB_PASSWORD`
- `MOVU_ROOT_DB_PASSWORD`
- `JWT_SECRET_KEY`, at least 32 characters
- `CORS_ORIGINS`
- `FRONTEND_BASE_URL`
- `PUBLIC_API_BASE_URL`
- `SMTP_HOST`
- `SMTP_FROM_EMAIL`
- `OSRM_BASE_URL`
- `REDIS_URL` when running more than one backend replica or sharing limits across instances

3. Build and start.

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

4. Check service health.

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl http://localhost:${BACKEND_PORT:-8000}/health
```

Default production host ports:

- Backend: `8000`
- Admin dashboard: `5173`
- User app: `5174`

Override with:

```env
BACKEND_PORT=8000
ADMIN_DASHBOARD_PORT=5173
USER_APP_PORT=5174
```

## Domains And HTTPS

For a public deployment, place a TLS reverse proxy such as Caddy, Nginx Proxy Manager, Traefik, or a cloud load balancer in front of these services.

Recommended public origins:

- `https://api.your-domain.com/api`
- `https://admin.your-domain.com`
- `https://app.your-domain.com`

Set:

```env
PUBLIC_API_BASE_URL=https://api.your-domain.com/api
CORS_ORIGINS=https://admin.your-domain.com,https://app.your-domain.com
FRONTEND_BASE_URL=https://app.your-domain.com
```

## Database Migrations

The backend container runs:

```bash
alembic upgrade head
```

before starting Uvicorn. If a migration fails, the backend container will fail instead of serving with a mismatched schema.

Manual migration command:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Production Guards

Production mode enforces:

- MySQL only, no SQLite
- strong JWT secret
- SMTP configuration for email verification
- OSRM configuration
- non-empty CORS origins
- no seed data
- no simulated payment completion
- coordinates required for ride requests and trips
- rider and driver core actions require admin-approved account status
- Redis-backed rate limiting when `REDIS_URL` is configured

Payment collection remains disabled until an approved payment provider is configured and certified.

## Smoke Test

After deployment:

```bash
curl http://localhost:${BACKEND_PORT:-8000}/health
```

Then verify in the browser:

- Register using a Taylor's email domain.
- Confirm SMTP email delivery.
- Admin approves the user and vehicle.
- Rider creates a request inside the 30km service area.
- Driver posts a trip inside the 30km service area.
- Match recommendations appear.
- SOS event appears in the admin dashboard.

## Rollback

If a release fails:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
git checkout <previous-good-commit>
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

Do not delete the `mysql_data` volume unless you intentionally want to remove production data.
