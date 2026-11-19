from dataclasses import dataclass

from .config import Config
from .layout import Box, Mover, Peg, Segment, combine
from .sections import SECTION_PLAN

START_Y = 220
BOTTOM_MARGIN = 160


@dataclass(frozen=True)
class Track:
    segments: tuple[Segment, ...]
    pegs: tuple[Peg, ...]
    movers: tuple[Mover, ...]
    boxes: tuple[Box, ...]
    start_y: float
    finish_y: float
    world_h: float


def _walls(cfg: Config, bottom: float) -> tuple[Segment, ...]:
    top = -3000
    return ((0, top, 0, bottom), (cfg.world_w, top, cfg.world_w, bottom))


def _stack_sections(cfg: Config) -> tuple:
    layouts, top = [], START_Y
    for section in SECTION_PLAN:
        layout = section(cfg, top)
        layouts.append(layout)
        top += layout.height
    return combine(layouts), top


def build_track(cfg: Config) -> Track:
    merged, finish_y = _stack_sections(cfg)
    world_h = finish_y + BOTTOM_MARGIN
    return Track(
        segments=_walls(cfg, world_h) + merged.segments,
        pegs=merged.pegs,
        movers=merged.movers,
        boxes=merged.boxes,
        start_y=START_Y,
        finish_y=finish_y,
        world_h=world_h,
    )