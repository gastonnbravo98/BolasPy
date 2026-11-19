import random
from dataclasses import dataclass
from enum import Enum

import pymunk

from .config import Config
from .players import Player
from .powerups import Context, PowerUp, build_powerups
from .track import Track
from .world import PhysicsWorld

Event = dict


class Phase(str, Enum):
    LOBBY = "lobby"
    RACING = "racing"
    FINISHED = "finished"


@dataclass
class Entry:
    player: Player
    body: pymunk.Body
    rank: int | None = None
    last_boost: float = float("-inf")
    still_for: float = 0.0
    held: str | None = None  # power-up guardado


@dataclass
class BoxState:
    index: int
    x: float
    y: float
    ready_at: float = 0.0


@dataclass
class ActiveEffect:
    entry: Entry
    powerup: PowerUp
    ends_at: float


class Race:
    """Reglas del juego: fases, cajas, power-ups, llegada y ranking."""

    def __init__(self, cfg: Config, track: Track, world: PhysicsWorld):
        self._cfg = cfg
        self._track = track
        self._world = world
        self.phase = Phase.LOBBY
        self.players: dict[str, Player] = {}
        self._entries: dict[str, Entry] = {}
        self._finish_order: list[Entry] = []
        self._elapsed = 0.0
        self._powerups = build_powerups(cfg)
        self._boxes = [BoxState(i, x, y) for i, (x, y) in enumerate(track.boxes)]
        self._effects: list[ActiveEffect] = []
        self._tickers = {
            Phase.LOBBY: lambda dt: [],
            Phase.RACING: self._tick_racing,
            Phase.FINISHED: self._tick_finished,
        }

    # ---- API pública -------------------------------------------------
    def join(self, player: Player) -> bool:
        is_new = player.id not in self.players
        if is_new and len(self.players) >= self._cfg.max_players:
            return False
        self.players[player.id] = player
        return True

    def has_marble(self, player_id: str) -> bool:
        return self.phase is Phase.RACING and player_id in self._entries

    def start(self) -> list[Event]:
        if self.phase is not Phase.LOBBY or not self.players:
            return []
        self._spawn_all()
        self._reset_round()
        return self._enter(Phase.RACING)

    def tick(self, dt: float) -> list[Event]:
        self._elapsed += dt
        return self._tickers[self.phase](dt)

    def boost(self, player_id: str, now: float) -> bool:
        entry = self._entries.get(player_id)
        if not self._can_boost(entry, now):
            return False
        entry.last_boost = now
        self._world.boost(entry.body, self._cfg.boost_speed)
        return True

    def use_powerup(self, player_id: str) -> list[Event]:
        entry = self._entries.get(player_id)
        if not self._can_use_powerup(entry):
            return []
        powerup = self._powerups[entry.held]
        if not powerup.apply(self._context(entry)):
            return []
        return [self._consume(entry, powerup)]

    def snapshot(self) -> dict:
        return {
            "marbles": [self._marble_state(e) for e in self._entries.values() if e.rank is None],
            "movers": self._world.mover_states(),
        }

    # ---- transiciones ------------------------------------------------
    def _enter(self, phase: Phase) -> list[Event]:
        self.phase = phase
        self._elapsed = 0.0
        return [{"type": "phase", "phase": phase.value, "players": len(self.players)}]

    def _reset_round(self) -> None:
        self._effects.clear()
        self._world.reset_movers()
        for box in self._boxes:
            box.ready_at = 0.0

    def _spawn_all(self) -> None:
        self._entries.clear()
        self._finish_order.clear()
        for index, player in enumerate(self.players.values()):
            body = self._world.spawn_marble(*self._spawn_point(index))
            self._entries[player.id] = Entry(player, body)

    def _spawn_point(self, index: int) -> tuple[float, float]:
        step = self._cfg.marble_radius * 2 + 2
        cols = int((self._cfg.world_w - 60) // step)
        return 30 + (index % cols) * step, self._track.start_y - 30 - (index // cols) * step

    # ---- ticks por fase ----------------------------------------------
    def _tick_racing(self, dt: float) -> list[Event]:
        self._world.step(dt)
        self._rescue_stuck(dt)
        self._expire_effects()
        events = self._collect_boxes() + self._collect_finishers()
        if self._is_over():
            events += self._finish_race()
        return events

    def _tick_finished(self, dt: float) -> list[Event]:
        if self._elapsed < self._cfg.return_to_lobby_s:
            return []
        self._entries.clear()
        return self._enter(Phase.LOBBY)

    # ---- cajas -------------------------------------------------------
    def _collect_boxes(self) -> list[Event]:
        hands = [e for e in self._entries.values() if e.rank is None]
        ready = [b for b in self._boxes if b.ready_at <= self._elapsed]
        taken = [self._take_box(box, hands) for box in ready]
        return [event for event in taken if event is not None]

    def _take_box(self, box: BoxState, hands: list[Entry]) -> Event | None:
        reach = (self._cfg.box_radius + self._cfg.marble_radius) ** 2
        entry = next((e for e in hands if e.held is None and self._within(e, box, reach)), None)
        if entry is None:
            return None
        entry.held = random.choice(list(self._powerups))
        box.ready_at = self._elapsed + self._cfg.box_respawn_s
        return {
            "type": "box_taken",
            "box": box.index,
            "id": entry.player.id,
            "kind": entry.held,
            "respawn_s": self._cfg.box_respawn_s,
        }

    @staticmethod
    def _within(entry: Entry, box: BoxState, reach_sq: float) -> bool:
        dx, dy = entry.body.position.x - box.x, entry.body.position.y - box.y
        return dx * dx + dy * dy <= reach_sq

    # ---- power-ups ---------------------------------------------------
    def _can_use_powerup(self, entry: Entry | None) -> bool:
        if entry is None or self.phase is not Phase.RACING:
            return False
        return entry.rank is None and entry.held is not None

    def _context(self, entry: Entry) -> Context:
        others = [e for e in self._entries.values() if e is not entry and e.rank is None]
        return Context(user=entry, others=others, world=self._world, cfg=self._cfg)

    def _consume(self, entry: Entry, powerup: PowerUp) -> Event:
        entry.held = None
        if powerup.duration > 0:
            self._effects.append(ActiveEffect(entry, powerup, self._elapsed + powerup.duration))
        pos = entry.body.position
        return {"type": "powerup_used", "id": entry.player.id, "kind": powerup.kind, "x": round(pos.x, 1), "y": round(pos.y, 1)}

    def _expire_effects(self) -> None:
        due = [a for a in self._effects if a.ends_at <= self._elapsed]
        self._effects = [a for a in self._effects if a not in due]
        for effect in due:
            effect.powerup.expire(self._context(effect.entry))

    # ---- llegada -----------------------------------------------------
    def _crossed_line(self, entry: Entry) -> bool:
        return entry.rank is None and entry.body.position.y > self._track.finish_y

    def _collect_finishers(self) -> list[Event]:
        crossed = [e for e in self._entries.values() if self._crossed_line(e)]
        crossed.sort(key=lambda e: e.body.position.y, reverse=True)
        return [self._mark_finished(e) for e in crossed]

    def _mark_finished(self, entry: Entry) -> Event:
        self._effects = [a for a in self._effects if a.entry is not entry]
        self._finish_order.append(entry)
        entry.rank = len(self._finish_order)
        self._world.remove(entry.body)
        return {"type": "finish", "rank": entry.rank, **entry.player.to_dict()}

    def _is_over(self) -> bool:
        everyone_done = all(e.rank is not None for e in self._entries.values())
        return everyone_done or self._elapsed >= self._cfg.race_timeout_s

    def _finish_race(self) -> list[Event]:
        for entry in self._entries.values():
            if entry.rank is None:
                self._world.remove(entry.body)
        self._effects.clear()
        podium = [{"rank": e.rank, **e.player.to_dict()} for e in self._finish_order[:3]]
        return [{"type": "results", "podium": podium}] + self._enter(Phase.FINISHED)

    # ---- helpers -----------------------------------------------------
    def _marble_state(self, entry: Entry) -> list:
        pos = entry.body.position
        radius = self._world.radius_of(entry.body)
        return [entry.player.id, round(pos.x, 1), round(pos.y, 1), round(radius, 1), entry.held]

    def _rescue_stuck(self, dt: float) -> None:
        active = [e for e in self._entries.values() if e.rank is None]
        for entry in active:
            still = entry.body.velocity.length < self._cfg.stuck_speed
            entry.still_for = entry.still_for + dt if still else 0.0
        stuck = [e for e in active if e.still_for >= self._cfg.stuck_after_s]
        for entry in stuck:
            self._world.unstick(entry.body, self._cfg.unstick_speed)
            entry.still_for = 0.0

    def _can_boost(self, entry: Entry | None, now: float) -> bool:
        if entry is None or entry.rank is not None or self.phase is not Phase.RACING:
            return False
        return now - entry.last_boost >= self._cfg.boost_cooldown_s