from dataclasses import dataclass, replace
from typing import Iterable

Segment = tuple[float, float, float, float]
Peg = tuple[float, float, float]
Box = tuple[float, float]


@dataclass(frozen=True)
class Mover:
    """Obstáculo dinámico: una barra que gira (spinner) o que va y viene (slider)."""

    kind: str  # "spinner" | "slider"
    x: float
    y: float
    length: float
    speed: float = 0.0  # spinner: rad/s · slider: frecuencia de la oscilación
    amplitude: float = 0.0  # solo slider: px que se desplaza hacia cada lado
    tilt: float = 0.0  # px de desnivel entre los dos extremos de la barra


@dataclass(frozen=True)
class Layout:
    """Geometría de un tramo de la pista."""

    segments: tuple[Segment, ...] = ()
    pegs: tuple[Peg, ...] = ()
    movers: tuple[Mover, ...] = ()
    boxes: tuple[Box, ...] = ()
    height: float = 0.0

    def mirrored(self, width: float) -> "Layout":
        return Layout(
            segments=tuple((width - x1, y1, width - x2, y2) for x1, y1, x2, y2 in self.segments),
            pegs=tuple((width - x, y, r) for x, y, r in self.pegs),
            movers=tuple(replace(m, x=width - m.x, tilt=-m.tilt, speed=-m.speed) for m in self.movers),
            boxes=tuple((width - x, y) for x, y in self.boxes),
            height=self.height,
        )


def combine(layouts: Iterable[Layout]) -> Layout:
    parts = list(layouts)
    return Layout(
        segments=tuple(s for p in parts for s in p.segments),
        pegs=tuple(g for p in parts for g in p.pegs),
        movers=tuple(m for p in parts for m in p.movers),
        boxes=tuple(b for p in parts for b in p.boxes),
        height=sum(p.height for p in parts),
    )