import asyncio
import contextlib
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import CONFIG
from .hub import Hub
from .network import join_url
from .qr import qr_png
from .race import Race
from .service import GameService
from .track import build_track
from .world import PhysicsWorld

STATIC = Path(__file__).resolve().parent.parent / "static"
PORT = int(os.getenv("PORT", "8000"))
JOIN_URL = join_url(PORT)


def build_service() -> GameService:
    track = build_track(CONFIG)
    race = Race(CONFIG, track, PhysicsWorld(CONFIG, track))
    return GameService(CONFIG, track, race, Hub(), JOIN_URL)


service = build_service()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"\n  Pantalla grande : http://localhost:{PORT}/\n  Link del QR     : {JOIN_URL}\n")
    task = asyncio.create_task(service.run())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def host_page() -> FileResponse:
    return FileResponse(STATIC / "host" / "index.html")


@app.get("/play")
def player_page() -> FileResponse:
    return FileResponse(STATIC / "play" / "index.html")


@app.get("/qr.png")
def qr() -> Response:
    return Response(qr_png(JOIN_URL), media_type="image/png")


@app.websocket("/ws/host")
async def ws_host(ws: WebSocket) -> None:
    await service.serve_host(ws)


@app.websocket("/ws/player")
async def ws_player(ws: WebSocket) -> None:
    await service.serve_player(ws)
