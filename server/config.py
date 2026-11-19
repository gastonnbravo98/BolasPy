from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # mundo
    world_w: int = 1000
    gravity: float = 900.0
    marble_radius: float = 12.0
    # zigzag (tramo de rampas)
    ramp_gap: float = 290.0
    ramp_drop: float = 180.0
    hole_width: float = 110.0
    # simulación
    tick_hz: int = 60
    broadcast_every: int = 2  # 1 de cada N ticks se envía a la pantalla
    # reglas
    max_players: int = 150
    boost_cooldown_s: float = 5.0
    boost_speed: float = 350.0
    race_timeout_s: float = 150.0
    return_to_lobby_s: float = 12.0
    # bolitas trabadas
    stuck_after_s: float = 1.5
    stuck_speed: float = 12.0
    unstick_speed: float = 260.0
    # cajas y power-ups
    box_radius: float = 22.0
    box_respawn_s: float = 8.0
    rocket_speed: float = 650.0
    giant_scale: float = 1.7
    giant_mass: float = 3.0
    giant_duration_s: float = 6.0
    shock_radius: float = 240.0
    shock_speed: float = 420.0


CONFIG = Config()