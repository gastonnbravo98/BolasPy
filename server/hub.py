import asyncio

from fastapi import WebSocket


class Hub:
    """Registro de conexiones y envío de mensajes. No conoce el juego."""

    def __init__(self):
        self._hosts: set[WebSocket] = set()
        self._players: dict[str, WebSocket] = {}

    def add_host(self, ws: WebSocket) -> None:
        self._hosts.add(ws)

    def bind_player(self, player_id: str, ws: WebSocket) -> None:
        self._players[player_id] = ws

    def drop(self, ws: WebSocket) -> None:
        self._hosts.discard(ws)
        self._players = {pid: w for pid, w in self._players.items() if w is not ws}

    def player_id_of(self, ws: WebSocket) -> str | None:
        return next((pid for pid, w in self._players.items() if w is ws), None)

    async def to_hosts(self, message: dict) -> None:
        await self._send_all(list(self._hosts), message)

    async def to_players(self, message: dict) -> None:
        await self._send_all(list(self._players.values()), message)

    async def to_player(self, player_id: str, message: dict) -> None:
        ws = self._players.get(player_id)
        if ws is not None:
            await self._safe_send(ws, message)

    async def _send_all(self, sockets: list[WebSocket], message: dict) -> None:
        await asyncio.gather(*(self._safe_send(ws, message) for ws in sockets))

    async def _safe_send(self, ws: WebSocket, message: dict) -> None:
        try:
            await ws.send_json(message)
        except Exception:
            self.drop(ws)
