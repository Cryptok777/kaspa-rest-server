# encoding: utf-8
import os
import traceback

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.routing import APIRoute

from kaspad.KaspadMultiClient import KaspadMultiClient
from fastapi.middleware.gzip import GZipMiddleware

from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])
socket_app = socketio.ASGIApp(sio)

Config.set(
    key=os.environ["SCOUT_KEY"],
    name="Kaspa Explorer API",
    monitor=True,
)

def custom_generate_unique_id(route: APIRoute):
    return f"{route.name}"


app = FastAPI(
    title="Kaspa REST-API server",
    description="This server is to communicate with kaspa network via REST-API",
    version="0.0.3",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(ScoutMiddleware)

app.mount("/ws", socket_app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


kaspad_hosts = []

for i in range(100):
    try:
        kaspad_hosts.append(os.environ[f"KASPAD_HOST_{i + 1}"].strip())
    except KeyError:
        break

if not kaspad_hosts:
    raise Exception("Please set at least KASPAD_HOST_1 environment variable.")

kaspad_client = KaspadMultiClient(kaspad_hosts)


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    await kaspad_client.initialize_all()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.on_event("startup")
@repeat_every(seconds=60)
async def periodical_blockdag():
    await kaspad_client.initialize_all()
