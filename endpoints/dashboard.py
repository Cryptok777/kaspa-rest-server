# encoding: utf-8
import os
import httpx

from fastapi import Response
from endpoints.block import get_block
from endpoints.holders import get_total_holders
from endpoints.models import (
    DashboardMetricsResponse,
    GraphsResponse,
    MarketResponse,
    SearchResponse,
    WhaleMovementResponse,
)
from endpoints.transaction import get_transaction
from helper.constants import KASPA_HASH_LENGTH, PRECISION
from server import app, kaspad_client, memory_cache
from dbsession import async_session
from sqlalchemy import text

from endpoints.stats import (
    _get_block_reward,
    get_coinsupply,
    get_halving,
    get_hashrate,
)

from server import app, kaspad_client
from cache import AsyncTTL


@AsyncTTL(time_to_live=60 * 60)
async def _get_max_tps():
    sql = f"""
                SELECT
                    value
                FROM agg_stats
                WHERE key = 'max_tps'
                ORDER BY created_at DESC
                LIMIT 1
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.first()

    if len(resp) == 0:
        return 0

    return resp[0]


@AsyncTTL(time_to_live=60 * 60)
async def _get_tps():
    sql = f"""
                SELECT
                    count
                FROM agg_tps
                LIMIT 1
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.first()

    if len(resp) == 0:
        return 0

    return resp[0]


@AsyncTTL(time_to_live=60 * 60)
async def _get_bps():
    sql = f"""
                SELECT
                    count
                FROM agg_bps
                LIMIT 1
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.first()

    if len(resp) == 0:
        return 0

    return resp[0]


@AsyncTTL(time_to_live=5)
async def _get_block_dag_info():
    return await kaspad_client.request("getBlockDagInfoRequest")


@AsyncTTL(time_to_live=5 * 60)
async def _get_max_hashrate():
    sql = f"""
                SELECT
                    MAX(difficulty) * 2
                FROM blocks
                LIMIT 1
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.first()

    if len(resp) == 0:
        return 0

    return resp[0]


@app.get(
    "/dashboard/metrics",
    response_model=DashboardMetricsResponse,
    tags=["dashboard"],
)
async def get_dashboard_metrics(use_cache: bool = True):
    if use_cache and "dashboard_metrics_cache" in memory_cache:
        return memory_cache["dashboard_metrics_cache"]

    dag_info = (await _get_block_dag_info()).get("getBlockDagInfoResponse")
    coin_supply_info = await get_coinsupply()
    halving_info = get_halving(dag_info)
    hashrate_info = get_hashrate(dag_info)
    max_supply = int(coin_supply_info.get("maxSupply", 0))
    current_supply = int(coin_supply_info.get("circulatingSupply", 0))
    tps = await _get_tps()
    max_tps = await _get_max_tps()
    bps = await _get_bps()
    current_addresses_count = await get_total_holders()
    max_hashrate = await _get_max_hashrate()

    return DashboardMetricsResponse(
        block_count=dag_info.get("blockCount"),
        header_count=dag_info.get("headerCount"),
        daa_score=dag_info.get("virtualDaaScore"),
        current_supply=current_supply / PRECISION,
        tps=tps,
        max_tps=max_tps,
        bps=bps,
        hashrate=hashrate_info.get("hashrate"),
        max_hashrate=max_hashrate,
        mined_pct=current_supply / max_supply * 100,
        current_reward=_get_block_reward(dag_info).get("blockreward"),
        next_halving_timestamp=halving_info.get("nextHalvingTimestamp") * 1e3,
        next_halving_reward=halving_info.get("nextHalvingAmount"),
        current_addresses_count=current_addresses_count,
    )


@AsyncTTL(time_to_live=5 * 60)
async def _get_market_data():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest",
            params={"slug": "kaspa"},
            headers={
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": os.environ["COINMARKETCAP_API_KEY"],
            },
        )

    if resp.status_code == 200 and resp.json().get("status", {}).get("error_code") == 0:
        resp = resp.json().get("data")
        first_key = list(resp.keys())[0]
        market_data = resp[first_key]
        quote = market_data.get("quote", {}).get("USD", {})

        return {
            "cmc_rank": market_data.get("cmc_rank"),
            "price": quote.get("price"),
            "price_pct_change_24h": quote.get("percent_change_24h"),
            "volume_24h": quote.get("volume_24h"),
            "market_cap": quote.get("market_cap"),
        }


@app.get(
    "/dashboard/market",
    response_model=MarketResponse,
    tags=["dashboard"],
)
async def get_market_data():
    """
    Get $KAS price and marke data
    """
    return await _get_market_data()


@AsyncTTL(time_to_live=3 * 60)
async def _get_whale_movement():
    sql = f"""
                SELECT
                    transaction_id
                    ,script_public_key_address
                    ,amount
                    ,block_time
                FROM agg_whale_movements
                ORDER BY block_time desc
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    tx_list = []
    for x in resp:
        tx_list.append(
            {
                "transaction_id": x[0],
                "receiver": x[1],
                "amount": x[2],
                "time": x[3],
            }
        )

    return {"transactions": tx_list}


@app.get(
    "/dashboard/whale_movement",
    response_model=WhaleMovementResponse,
    tags=["dashboard"],
)
async def get_whale_movement():
    return await _get_whale_movement()


async def _get_active_address_graph():
    sql = f"""
                SELECT  
                    date
                    ,count
                FROM agg_active_addresses
                WHERE date > current_date - interval '90' day
                ORDER BY date ASC;
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    result = []
    for x in resp:
        result.append(
            {
                "x": x[0].strftime("%Y-%m-%d"),
                "y": x[1],
            }
        )

    return result


async def _get_tx_count_graph():
    sql = f"""
                SELECT  
                    date
                    ,count
                FROM agg_transactions_count
                WHERE date > current_date - interval '90' day
                ORDER BY date ASC;
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    result = []
    for x in resp:
        result.append(
            {
                "x": x[0].strftime("%Y-%m-%d"),
                "y": x[1],
            }
        )

    return result


@AsyncTTL(time_to_live=30 * 60)
async def _get_dashboard_graphs():
    active_address_graph = await _get_active_address_graph()
    tx_count_graph = await _get_tx_count_graph()
    return {"active_address": active_address_graph, "tx_count": tx_count_graph}


@app.get(
    "/dashboard/graphs",
    response_model=GraphsResponse,
    tags=["dashboard"],
)
async def get_dashboard_graphs():
    resp = await _get_dashboard_graphs()
    return resp


@app.get(
    "/dashboard/search",
    response_model=SearchResponse,
    tags=["dashboard"],
)
async def get_search_result(query: str):
    query = query.strip().lower()

    if query.startswith("kaspa"):
        return {"result_type": "address", "value": query}

    try:
        if len(query) != KASPA_HASH_LENGTH:
            raise Exception()
        await get_block(response=Response(), blockId=query)
        return {"result_type": "block", "value": query}
    except:
        pass

    try:
        if len(query) != KASPA_HASH_LENGTH:
            raise Exception()
        await get_transaction(transactionId=query, inputs=False, outputs=False)
        return {"result_type": "transaction", "value": query}
    except:
        pass

    return {"result_type": "", "value": query}
