# encoding: utf-8
from typing import List

from fastapi import Query, Path, HTTPException
from endpoints.models import BlockModel, BlockResponse

from server import app, kaspad_client


@app.get("/blocks/{blockId}", response_model=BlockModel, tags=["Kaspa blocks"])
async def get_block(blockId: str = Path(regex="[a-f0-9]{64}")):
    """
    Get block information for a given block id
    """
    resp = await kaspad_client.request(
        "getBlockRequest", params={"hash": blockId, "includeTransactions": True}
    )
    try:
        return resp["getBlockResponse"]["block"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Block not found")


@app.get("/blocks", response_model=BlockResponse, tags=["Kaspa blocks"])
async def get_blocks(
    lowHash: str = Query(regex="[a-f0-9]{64}"),
    includeBlocks: bool = False,
    includeTransactions: bool = False,
):
    """
    Lists block beginning from a low hash (block id)
    """
    resp = await kaspad_client.request(
        "getBlocksRequest",
        params={
            "lowHash": lowHash,
            "includeBlocks": includeBlocks,
            "includeTransactions": includeTransactions,
        },
    )

    return resp["getBlocksResponse"]
