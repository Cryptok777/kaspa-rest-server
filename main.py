# encoding: utf-8
import asyncio
import os
from asyncio import Task, InvalidStateError

from helper.import_endpoints import *
from fastapi_utils.tasks import repeat_every
from starlette.responses import RedirectResponse

from server import app, kaspad_client
from sockets import blocks

BLOCKS_TASK = None  # type: Task


@app.on_event("startup")
async def startup():
    global BLOCKS_TASK
    # find kaspad before staring webserver
    await kaspad_client.initialize_all()
    BLOCKS_TASK = asyncio.create_task(blocks.config())


@app.on_event("startup")
@repeat_every(seconds=5)
async def watchdog():
    global BLOCKS_TASK

    try:
        exception = BLOCKS_TASK.exception()
    except InvalidStateError:
        pass
    else:
        print(
            f"Watch found an error! {exception}\n"
            f"Reinitialize kaspads and start task again"
        )
        await kaspad_client.initialize_all()
        BLOCKS_TASK = asyncio.create_task(blocks.config())


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    if os.getenv("DEBUG"):
        import uvicorn

        uvicorn.run(app)
