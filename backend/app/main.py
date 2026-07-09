from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, location, matches, network, notifications, payments, reports, ride_requests, sos, trips, users, vehicles
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware


app = FastAPI(title=settings.app_name)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(location.router, prefix=settings.api_prefix)
app.include_router(location.ws_router)
app.include_router(matches.router, prefix=settings.api_prefix)
app.include_router(network.router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(ride_requests.router, prefix=settings.api_prefix)
app.include_router(sos.router, prefix=settings.api_prefix)
app.include_router(sos.ws_router)
app.include_router(trips.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(vehicles.router, prefix=settings.api_prefix)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
