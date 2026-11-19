import asyncio
import logging
import time
from dataclasses import asdict

from fastapi import WebSocket, WebSocketDisconnect

from .config import Config
from .hub import Hub
from .players import Player, clean_color, clean_name, color_for
from .race import Phase, Race
from .track import Track

log = logging.getLogger("marbles")


class GameService:
    """Orquesta: recibe mensajes, avanza la carrera y reparte eventos."""

    def __init__(self, cfg: Config, track: Track, race: Race, hub: Hub, join_url: str):
        self._cfg = cfg
        self._track = track
        self._race = race
        self._hub = hub
        self._join_url = join_url
        self._host_handlers = {"start": self._host_start}
        self._player_handlers = {
            "join": self._player_join,
            "boost": self._player_boost,
            "use": self._player_use,
        }
        self._event_routes = {
            "phase": self._route_phase,
            "finish": self._route_finish,
            "results": self._route_results,
            "box_taken": self._route_box_taken,
            "powerup_used": self._route_powerup_used,
        }

    # ---- sockets -----------------------------------------------------
    async def serve_host(self, ws: WebSocket) -> None:
        await ws.accept()
        self._hub.add_host(ws)
        await ws.send_json(self._init_message())
        await self._listen(ws, self._host_handlers)

    async def serve_player(self, ws: WebSocket) -> None:
        await ws.accept()
        await self._listen(ws, self._player_handlers)

    async def _listen(self, ws: WebSocket, handlers: dict) -> None:
        try:
            while True:
                await self._route(handlers, ws, await ws.receive_json())
        except (WebSocketDisconnect, RuntimeError, ValueError):
            pass
        finally:
            self._hub.drop(ws)

    async def _route(self, handlers: dict, ws: WebSocket, message: object) -> None:
        if not isinstance(message, dict):
            return
        handler = handlers.get(message.get("type"))
        if handler is not None:
            await handler(ws, message)

    # ---- handlers de la pantalla ------------------------------------
    async def _host_start(self, ws: WebSocket, message: dict) -> None:
        await self._dispatch(self._race.start())

    # ---- handlers de los celulares ----------------------------------
    async def _player_join(self, ws: WebSocket, message: dict) -> None:
        player_id = str(message.get("id", ""))[:64]
        if not player_id:
            return
        color = clean_color(message.get("color"), color_for(player_id))
        player = Player(player_id, clean_name(message.get("name", "")), color)
        if not self._race.join(player):
            await ws.send_json({"type": "error", "reason": "full"})
            return
        self._hub.bind_player(player_id, ws)
        await ws.send_json(self._joined_message(player))
        await self._hub.to_hosts(
            {"type": "player_joined", "player": player.to_dict(), "count": len(self._race.players)}
        )

    async def _player_boost(self, ws: WebSocket, message: dict) -> None:
        player_id = self._hub.player_id_of(ws)
        ok = player_id is not None and self._race.boost(player_id, time.monotonic())
        await ws.send_json({"type": "boost", "ok": ok, "cooldown": self._cfg.boost_cooldown_s})

    async def _player_use(self, ws: WebSocket, message: dict) -> None:
        player_id = self._hub.player_id_of(ws)
        if player_id is not None:
            await self._dispatch(self._race.use_powerup(player_id))

    # ---- mensajes ----------------------------------------------------
    def _init_message(self) -> dict:
        return {
            "type": "init",
            "config": {
                "world_w": self._cfg.world_w,
                "world_h": self._track.world_h,
                "radius": self._cfg.marble_radius,
                "finish_y": self._track.finish_y,
                "box_radius": self._cfg.box_radius,
                "shock_radius": self._cfg.shock_radius,
            },
            "track": {
                "segments": [list(s) for s in self._track.segments],
                "pegs": [list(p) for p in self._track.pegs],
                "movers": [asdict(m) for m in self._track.movers],
                "boxes": [list(b) for b in self._track.boxes],
            },
            "phase": self._race.phase.value,
            "players": [p.to_dict() for p in self._race.players.values()],
            "join_url": self._join_url,
        }

    def _joined_message(self, player: Player) -> dict:
        return {
            "type": "joined",
            "name": player.name,
            "color": player.color,
            "phase": self._race.phase.value,
            "in_race": self._race.has_marble(player.id),
        }

    # ---- eventos de la carrera --------------------------------------
    async def _dispatch(self, events: list[dict]) -> None:
        for event in events:
            await self._event_routes[event["type"]](event)

    async def _route_phase(self, event: dict) -> None:
        await self._hub.to_hosts(event)
        await self._hub.to_players(event)

    async def _route_finish(self, event: dict) -> None:
        await self._hub.to_hosts(event)
        await self._hub.to_player(event["id"], {"type": "finish", "rank": event["rank"]})

    async def _route_results(self, event: dict) -> None:
        await self._hub.to_hosts(event)

    async def _route_box_taken(self, event: dict) -> None:
        await self._hub.to_hosts(event)
        await self._hub.to_player(event["id"], {"type": "powerup", "kind": event["kind"]})

    async def _route_powerup_used(self, event: dict) -> None:
        await self._hub.to_hosts(event)
        await self._hub.to_player(event["id"], {"type": "powerup", "kind": None})

    # ---- bucle principal --------------------------------------------
    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        dt = 1 / self._cfg.tick_hz
        next_tick, frame = loop.time(), 0
        while True:
            await self._safe_step(dt, frame)
            frame += 1
            next_tick += dt
            await asyncio.sleep(max(0.0, next_tick - loop.time()))

    async def _safe_step(self, dt: float, frame: int) -> None:
        try:
            await self._step(dt, frame)
        except Exception:
            log.exception("error en el tick")

    async def _step(self, dt: float, frame: int) -> None:
        await self._dispatch(self._race.tick(dt))
        if self._race.phase is Phase.RACING and frame % self._cfg.broadcast_every == 0:
            await self._hub.to_hosts({"type": "snapshot", **self._race.snapshot()})