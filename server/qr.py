from functools import lru_cache
from io import BytesIO

import qrcode


@lru_cache(maxsize=4)
def qr_png(url: str) -> bytes:
    buffer = BytesIO()
    qrcode.make(url, box_size=12, border=2).save(buffer, format="PNG")
    return buffer.getvalue()
