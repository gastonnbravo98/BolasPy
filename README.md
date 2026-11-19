# Carrera de bolitas para charlas

Python (FastAPI + pymunk) simula la física. PixiJS dibuja en la pantalla grande.
El público escanea un QR y entra desde el celular.

## Correr
    pip install -r requirements.txt
    python run.py

- Pantalla grande (proyector): http://localhost:8000/   (tecla ESPACIO = largar)
- El QR apunta a la IP local de tu compu. Los celulares deben estar en la misma wifi.

## Si la wifi del lugar aísla los dispositivos
Usá un túnel y pasale la URL pública:

    cloudflared tunnel --url http://localhost:8000
    PUBLIC_URL=https://xxxx.trycloudflare.com python run.py

## Ajustes
Todo está en `server/config.py` (cantidad de rampas, gravedad, cooldown del impulso, etc.).
