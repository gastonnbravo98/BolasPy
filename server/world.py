import math
import random

import pymunk

from .config import Config
from .layout import Mover
from .track import Track

ELASTICITY = 0.5
TRACK_FRICTION = 0.3
MARBLE_FRICTION = 0.15
MOVER_THICKNESS = 5


def _with_material(shape: pymunk.Shape, friction: float) -> pymunk.Shape:
    shape.elasticity = ELASTICITY
    shape.friction = friction
    return shape


# ---- cómo se mueve cada tipo de obstáculo ----------------------------------
def _drive_spinner(spec: Mover, body: pymunk.Body, t: float) -> None:
    body.angular_velocity = spec.speed


def _drive_slider(spec: Mover, body: pymunk.Body, t: float) -> None:
    body.velocity = (spec.amplitude * spec.speed * math.cos(spec.speed * t), 0)


DRIVERS = {"spinner": _drive_spinner, "slider": _drive_slider}


class PhysicsWorld:
    """Envuelve pymunk. No conoce jugadores ni reglas, solo física."""

    def __init__(self, cfg: Config, track: Track):
        self._cfg = cfg
        self._space = pymunk.Space()
        self._space.gravity = (0, cfg.gravity)
        self._movers: list[tuple[Mover, pymunk.Body]] = []
        self._clock = 0.0
        self._add_track(track)
        self._add_movers(track.movers)

    # ---- construcción ------------------------------------------------------
    def _add_track(self, track: Track) -> None:
        static = self._space.static_body
        segments = [pymunk.Segment(static, (x1, y1), (x2, y2), 4) for x1, y1, x2, y2 in track.segments]
        pegs = [pymunk.Circle(static, r, (x, y)) for x, y, r in track.pegs]
        self._space.add(*[_with_material(s, TRACK_FRICTION) for s in segments + pegs])

    def _add_movers(self, specs: tuple[Mover, ...]) -> None:
        self._movers = [(spec, self._build_mover(spec)) for spec in specs]

    def _build_mover(self, spec: Mover) -> pymunk.Body:
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (spec.x, spec.y)
        half = spec.length / 2
        shape = pymunk.Segment(body, (-half, -spec.tilt / 2), (half, spec.tilt / 2), MOVER_THICKNESS)
        self._space.add(body, _with_material(shape, TRACK_FRICTION))
        return body

    # ---- obstáculos dinámicos -------------------------------------------------
    def reset_movers(self) -> None:
        self._clock = 0.0
        for spec, body in self._movers:
            body.position = (spec.x, spec.y)
            body.angle = 0.0
        self._drive()

    def _drive(self) -> None:
        for spec, body in self._movers:
            DRIVERS[spec.kind](spec, body, self._clock)

    def mover_states(self) -> list[list[float]]:
        return [[round(b.position.x, 1), round(b.position.y, 1), round(b.angle, 3)] for _, b in self._movers]

    # ---- bolitas ------------------------------------------------------------------
    def spawn_marble(self, x: float, y: float) -> pymunk.Body:
        radius, mass = self._cfg.marble_radius, 1.0
        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        body.position = (x, y)
        body.velocity = (random.uniform(-40, 40), 0)
        self._space.add(body, _with_material(pymunk.Circle(body, radius), MARBLE_FRICTION))
        return body

    def remove(self, body: pymunk.Body) -> None:
        self._space.remove(body, *body.shapes)

    def radius_of(self, body: pymunk.Body) -> float:
        return next(iter(body.shapes)).radius

    def resize(self, body: pymunk.Body, radius: float, mass: float) -> None:
        next(iter(body.shapes)).unsafe_set_radius(radius)
        body.mass = mass
        body.moment = pymunk.moment_for_circle(mass, 0, radius)

    # ---- empujones --------------------------------------------------------------
    def push(self, body: pymunk.Body, impulse: tuple[float, float]) -> None:
        body.apply_impulse_at_world_point(impulse, body.position)

    def boost(self, body: pymunk.Body, speed: float) -> None:
        direction = 1 if body.velocity.x >= 0 else -1
        self.push(body, (direction * speed, -speed * 0.4))

    def unstick(self, body: pymunk.Body, speed: float) -> None:
        self.push(body, (random.choice((-1, 1)) * speed, -speed * 0.5))

    def swap(self, a: pymunk.Body, b: pymunk.Body) -> None:
        a.position, b.position = b.position, a.position
        a.velocity, b.velocity = b.velocity, a.velocity

    def step(self, dt: float) -> None:
        self._clock += dt
        self._drive()
        self._space.step(dt)