import colorsys
import hashlib
import re
from dataclasses import asdict, dataclass

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    color: str

    def to_dict(self) -> dict:
        return asdict(self)


def color_for(player_id: str) -> str:
    hue = int(hashlib.md5(player_id.encode()).hexdigest()[:4], 16) / 0xFFFF
    r, g, b = colorsys.hls_to_rgb(hue, 0.58, 0.85)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def clean_color(raw: object, fallback: str) -> str:
    value = str(raw or "")
    return value.lower() if HEX_COLOR.match(value) else fallback


def clean_name(raw: object, limit: int = 16) -> str:
    name = " ".join(str(raw).split())[:limit]
    return name or "Anónimo"