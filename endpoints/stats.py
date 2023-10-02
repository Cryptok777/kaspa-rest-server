# encoding: utf-8
import time
from datetime import datetime

import hashlib
from endpoints.models import (
    BlockRewardResponse,
    BlockdagResponse,
    CoinSupplyResponse,
    HealthResponse,
    NetworkResponse,
)
from server import app, kaspad_client

from helper.deflationary_table import DEFLATIONARY_TABLE
from cache import AsyncTTL

PREFIX = "info"


@app.get(f"/{PREFIX}/blockdag", tags=["Kaspa network info"])
async def get_blockdag():
    """
    Get some global Kaspa BlockDAG information
    """
    resp = await kaspad_client.request("getBlockDagInfoRequest")
    return resp["getBlockDagInfoResponse"]


def _get_block_reward(dag_info):
    daa_score = int(dag_info["virtualDaaScore"])
    reward = 0

    for to_break_score in sorted(DEFLATIONARY_TABLE):
        reward = DEFLATIONARY_TABLE[to_break_score]
        if daa_score < to_break_score:
            break

    return {"blockreward": reward}


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
    return _get_block_reward(resp["getBlockDagInfoResponse"])


@AsyncTTL(time_to_live=5)
async def _get_coin_supply():
    return await kaspad_client.request("getCoinSupplyRequest")


@app.get(
    f"/{PREFIX}/coinsupply",
    response_model=CoinSupplyResponse,
    tags=["Kaspa network info"],
)
async def get_coinsupply():
    """
    Get $KAS coin supply information
    """
    resp = await _get_coin_supply()
    return {
        "circulatingSupply": resp["getCoinSupplyResponse"]["circulatingSompi"],
        "maxSupply": resp["getCoinSupplyResponse"]["maxSompi"],
    }


def get_halving(dag_info):
    daa_score = int(dag_info["virtualDaaScore"])

    future_reward = 0
    daa_breakpoint = 0

    daa_list = sorted(DEFLATIONARY_TABLE)

    for i, to_break_score in enumerate(daa_list):
        if daa_score < to_break_score:
            future_reward = DEFLATIONARY_TABLE[daa_list[i + 1]]
            daa_breakpoint = to_break_score
            break

    next_halving_timestamp = int(time.time() + (daa_breakpoint - daa_score))

    return {
        "nextHalvingTimestamp": next_halving_timestamp,
        "nextHalvingDate": datetime.utcfromtimestamp(next_halving_timestamp).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
        "nextHalvingAmount": future_reward,
    }


def get_hashrate(dag_info):
    hashrate = dag_info.get("difficulty") * 2
    return {"hashrate": hashrate}


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
