import random
from dataclasses import dataclass

from pymunk import Vec2d

from .config import Config
from .world import PhysicsWorld


@dataclass
class Context:
    user: object  # Entry de la carrera (usa .body)
    others: list  # Entries de las demás bolitas que siguen corriendo
    world: PhysicsWorld
    cfg: Config


class PowerUp:
    """Base. apply() devuelve False si no pudo usarse (y no se gasta)."""

    kind = ""
    duration = 0.0  # 0 = efecto instantáneo

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def apply(self, ctx: Context) -> bool:
        raise NotImplementedError

    def expire(self, ctx: Context) -> None:
        return None


class Rocket(PowerUp):
    kind = "rocket"

    def apply(self, ctx: Context) -> bool:
        ctx.world.boost(ctx.user.body, self.cfg.rocket_speed)
        return True


class Giant(PowerUp):
    kind = "giant"

    @property
    def duration(self) -> float:
        return self.cfg.giant_duration_s

    def apply(self, ctx: Context) -> bool:
        radius = self.cfg.marble_radius * self.cfg.giant_scale
        ctx.world.resize(ctx.user.body, radius, self.cfg.giant_mass)
        return True

    def expire(self, ctx: Context) -> None:
        ctx.world.resize(ctx.user.body, self.cfg.marble_radius, 1.0)


class Shockwave(PowerUp):
    kind = "shockwave"

    def apply(self, ctx: Context) -> bool:
        center = ctx.user.body.position
        near = [o for o in ctx.others if (o.body.position - center).length < self.cfg.shock_radius]
        for other in near:
            self._push_away(ctx, other, center)
        return True

    def _push_away(self, ctx: Context, other, center: Vec2d) -> None:
        direction = (other.body.position - center).normalized()
        speed = self.cfg.shock_speed
        ctx.world.push(other.body, (direction.x * speed, direction.y * speed - speed * 0.3))


class Swap(PowerUp):
    kind = "swap"

    def apply(self, ctx: Context) -> bool:
        my_y = ctx.user.body.position.y
        ahead = [o for o in ctx.others if o.body.position.y > my_y]
        if not ahead:
            return False
        ctx.world.swap(ctx.user.body, random.choice(ahead).body)
        return True


ALL_POWERUPS = (Rocket, Giant, Shockwave, Swap)


def build_powerups(cfg: Config) -> dict[str, PowerUp]:
    return {cls.kind: cls(cfg) for cls in ALL_POWERUPS}