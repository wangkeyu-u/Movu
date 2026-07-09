from collections import defaultdict, deque
from time import monotonic
from typing import Any

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._redis: Any | None = None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if settings.environment == "test":
            return await call_next(request)

        client_host = self._client_host(request)
        key = f"{client_host}:{request.url.path}"
        if settings.redis_url:
            allowed = await self._allow_with_redis(key)
        else:
            allowed = self._allow_in_memory(key)
        if not allowed:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
        return await call_next(request)

    def _allow_in_memory(self, key: str) -> bool:
        now = monotonic()
        window_start = now - settings.rate_limit_window_seconds
        timestamps = self._requests[key]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
        if len(timestamps) >= settings.rate_limit_requests:
            return False
        timestamps.append(now)
        return True

    async def _allow_with_redis(self, key: str) -> bool:
        if self._redis is None:
            try:
                from redis import asyncio as redis_asyncio
            except ImportError as exc:
                raise RuntimeError("redis package is required when REDIS_URL is configured") from exc
            self._redis = redis_asyncio.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

        window = settings.rate_limit_window_seconds
        redis_key = f"movu:rate-limit:{key}:{int(monotonic() // window)}"
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, window)
        return count <= settings.rate_limit_requests

    @staticmethod
    def _client_host(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip() or "unknown"
        return request.client.host if request.client else "unknown"
