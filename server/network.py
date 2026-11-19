import os
import socket


def lan_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))  # no envía nada, solo elige la interfaz
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def join_url(port: int) -> str:
    """PUBLIC_URL tiene prioridad (ej. un túnel de cloudflared o ngrok)."""
    base = os.getenv("PUBLIC_URL") or f"http://{lan_ip()}:{port}"
    return base.rstrip("/") + "/play"
