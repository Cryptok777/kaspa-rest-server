# encoding: utf-8
import time
from datetime import datetime

from starlette.responses import PlainTextResponse
import hashlib
from endpoints.models import (
    BlockRewardResponse,
    BlockdagResponse,
    CoinSupplyResponse,
    HalvingResponse,
    HashrateResponse,
    HealthResponse,
    KaspadInfoResponse,
    NetworkResponse,
)
from server import app, kaspad_client

from helper.deflationary_table import DEFLATIONARY_TABLE
from fastapi.responses import PlainTextResponse

PREFIX = "info"


@app.get(
    f"/{PREFIX}/blockdag", response_model=BlockdagResponse, tags=["Kaspa network info"]
)
async def get_blockdag():
    """
    Get some global Kaspa BlockDAG information
    """
    resp = await kaspad_client.request("getBlockDagInfoRequest")
    return resp["getBlockDagInfoResponse"]


@app.get(
    f"/{PREFIX}/blockreward",
    response_model=BlockRewardResponse | str,
    tags=["Kaspa network info"],
)
async def get_blockreward(stringOnly: bool = False):
    """
    Returns the current blockreward in KAS/block
    """
    resp = await kaspad_client.request("getBlockDagInfoRequest")
    daa_score = int(resp["getBlockDagInfoResponse"]["virtualDaaScore"])

    reward = 0

    for to_break_score in sorted(DEFLATIONARY_TABLE):
        reward = DEFLATIONARY_TABLE[to_break_score]
        if daa_score < to_break_score:
            break

    if not stringOnly:
        return {"blockreward": reward}

    else:
        return f"{reward:.2f}"


@app.get(
    f"/{PREFIX}/coinsupply",
    response_model=CoinSupplyResponse,
    tags=["Kaspa network info"],
)
async def get_coinsupply():
    """
    Get $KAS coin supply information
    """
    resp = await kaspad_client.request("getCoinSupplyRequest")
    return {
        "circulatingSupply": resp["getCoinSupplyResponse"]["circulatingSompi"],
        "maxSupply": resp["getCoinSupplyResponse"]["maxSompi"],
    }


@app.get(
    f"/{PREFIX}/halving",
    response_model=HalvingResponse | str,
    tags=["Kaspa network info"],
)
async def get_halving(field: str | None = None):
    """
    Returns information about chromatic halving
    """
    resp = await kaspad_client.request("getBlockDagInfoRequest")
    daa_score = int(resp["getBlockDagInfoResponse"]["virtualDaaScore"])

    future_reward = 0
    daa_breakpoint = 0

    daa_list = sorted(DEFLATIONARY_TABLE)

    for i, to_break_score in enumerate(daa_list):
        if daa_score < to_break_score:
            future_reward = DEFLATIONARY_TABLE[daa_list[i + 1]]
            daa_breakpoint = to_break_score
            break

    next_halving_timestamp = int(time.time() + (daa_breakpoint - daa_score))

    if field == "nextHalvingTimestamp":
        return PlainTextResponse(content=str(next_halving_timestamp))

    elif field == "nextHalvingDate":
        return PlainTextResponse(
            content=datetime.utcfromtimestamp(next_halving_timestamp).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

    elif field == "nextHalvingAmount":
        return PlainTextResponse(content=str(future_reward))

    else:
        return {
            "nextHalvingTimestamp": next_halving_timestamp,
            "nextHalvingDate": datetime.utcfromtimestamp(
                next_halving_timestamp
            ).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "nextHalvingAmount": future_reward,
        }


@app.get(
    f"/{PREFIX}/hashrate",
    response_model=HashrateResponse | str,
    tags=["Kaspa network info"],
)
async def get_hashrate(stringOnly: bool = False):
    """
    Returns the current hashrate for Kaspa network in TH/s.
    """

    resp = await kaspad_client.request("getBlockDagInfoRequest")
    hashrate = resp["getBlockDagInfoResponse"]["difficulty"] * 2
    hashrate_in_th = hashrate / 1_000_000_000_000

    if not stringOnly:
        return {"hashrate": hashrate_in_th}

    else:
        return f"{hashrate_in_th:.01f}"


@app.get(
    f"/{PREFIX}/kaspad", response_model=KaspadInfoResponse, tags=["Kaspa network info"]
)
async def get_kaspad_info():
    """
    Get some information for kaspad instance, which is currently connected.
    """
    resp = await kaspad_client.request("getInfoRequest")
    p2p_id = resp["getInfoResponse"].pop("p2pId")
    resp["getInfoResponse"]["p2pIdHashed"] = hashlib.sha256(p2p_id.encode()).hexdigest()
    return resp["getInfoResponse"]


@app.get(
    f"/{PREFIX}/network", response_model=NetworkResponse, tags=["Kaspa network info"]
)
async def get_network():
    """
    Get some global kaspa network information
    """
    resp = await kaspad_client.request("getBlockDagInfoRequest")
    return resp["getBlockDagInfoResponse"]


@app.get(
    f"/{PREFIX}/virtual-chain-blue-score",
    response_model=BlockdagResponse,
    tags=["Kaspa network info"],
)
async def get_virtual_selected_parent_blue_score():
    """
    Returns the blue score of virtual selected parent
    """
    resp = await kaspad_client.request("getVirtualSelectedParentBlueScoreRequest")
    return resp["getVirtualSelectedParentBlueScoreResponse"]


@app.get(
    f"/{PREFIX}/health", response_model=HealthResponse, tags=["Kaspa network info"]
)
async def health_state():
    """
    Returns the current hashrate for Kaspa network in TH/s.
    """
    await kaspad_client.initialize_all()

    kaspads = []

    for i, kaspad_info in enumerate(kaspad_client.kaspads):
        kaspads.append(
            {
                "isSynced": kaspad_info.is_synced,
                "isUtxoIndexed": kaspad_info.is_utxo_indexed,
                "p2pId": hashlib.sha256(kaspad_info.p2p_id.encode()).hexdigest(),
                "kaspadHost": f"KASPAD_HOST_{i + 1}",
                "serverVersion": kaspad_info.server_version,
            }
        )

    return {"kaspadServers": kaspads}
