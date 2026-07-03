from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._trip_connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, trip_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._trip_connections[trip_id].add(websocket)

    def disconnect(self, trip_id: int, websocket: WebSocket) -> None:
        self._trip_connections[trip_id].discard(websocket)
        if not self._trip_connections[trip_id]:
            self._trip_connections.pop(trip_id, None)

    async def broadcast_trip_location(self, trip_id: int, message: dict) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in self._trip_connections.get(trip_id, set()):
            try:
                await websocket.send_json(message)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(trip_id, websocket)


location_manager = ConnectionManager()


class AdminAlertManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in self._connections:
            try:
                await websocket.send_json(message)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(websocket)


sos_alert_manager = AdminAlertManager()
