# encoding: utf-8
import os
import requests

import datetime, time
from endpoints.models import (
    DashboardMetricsResponse,
    GraphsResponse,
    MarketResponse,
    WhaleMovementResponse,
)
from server import app, kaspad_client
from dbsession import async_session
from sqlalchemy import text

from endpoints.stats import (
    get_coinsupply,
    get_halving,
    get_hashrate,
)

from server import app, kaspad_client
from cache import AsyncTTL

CACHE_MAX_SIZE = 10240
PRECISION = 1e8
MAX_SUPPLY = 2900000000000000000
WHALE_TX_THRESHHOLD = 1 * 1e6 * PRECISION


@app.get(
    "/dashboard/metrics",
    response_model=DashboardMetricsResponse,
    tags=["dashboard"],
)
async def get_dashboard_metrics():
    dag_info = (await kaspad_client.request("getBlockDagInfoRequest")).get(
        "getBlockDagInfoResponse"
    )

    coin_supply_info = await get_coinsupply()
    halving_info = get_halving(dag_info)
    hashrate_info = get_hashrate(dag_info)
    current_supply = int(coin_supply_info.get("circulatingSupply", 0))

    return DashboardMetricsResponse(
        block_count=dag_info.get("blockCount"),
        daa_score=dag_info.get("virtualDaaScore"),
        current_supply=current_supply / 1e9,
        tps=1.4,
        hashrate=hashrate_info.get("hashrate"),
        mined_pct=current_supply / MAX_SUPPLY * 100,
        next_halving_timestamp=halving_info.get("nextHalvingTimestamp"),
        next_halving_reward=halving_info.get("nextHalvingAmount"),
    )


def _get_market_data_cached():
    resp = requests.get(
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


@AsyncTTL(time_to_live=5 * 60, maxsize=CACHE_MAX_SIZE)
@app.get(
    "/dashboard/market",
    response_model=MarketResponse,
    tags=["dashboard"],
)
async def get_market_data():
    """
    Get $KAS price and marke data
    """
    return _get_market_data_cached()


@AsyncTTL(time_to_live=5 * 60, maxsize=CACHE_MAX_SIZE)
async def _get_whale_movement():
    date_range = datetime.datetime.now() - datetime.timedelta(days=1)
    date_range_unix = (
        time.mktime(date_range.timetuple()) * 1000 + date_range.microsecond / 1000
    )

    sql = f"""
                SELECT
                    transactions_outputs.transaction_id
                    ,transactions_outputs.script_public_key_address
                    ,transactions_outputs.amount
                    ,transactions.block_time
                FROM transactions_outputs
                LEFT JOIN transactions
                ON transactions.transaction_id = transactions_outputs.transaction_id
                WHERE
                    TRUE
                    AND transactions_outputs.amount > {WHALE_TX_THRESHHOLD}
                    AND transactions.block_time > {date_range_unix}
                ORDER BY transactions.block_time DESC
                LIMIT 100
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
                "amount": x[2] / PRECISION,
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
                    DATE_TRUNC('day',TO_TIMESTAMP(transactions.block_time/ 1e3)) as date
                    ,COUNT(DISTINCT(transactions_outputs.script_public_key_address))
                FROM transactions_outputs
                LEFT JOIN transactions
                ON transactions.transaction_id = transactions_outputs.transaction_id
                GROUP BY  DATE_TRUNC('day',TO_TIMESTAMP(transactions.block_time / 1e3))
                ORDER BY date
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
                SELECT  DATE_TRUNC('day',TO_TIMESTAMP(transactions.block_time/ 1e3)) AS date
                    ,COUNT(*)
                FROM transactions
                GROUP BY  DATE_TRUNC('day',TO_TIMESTAMP(transactions.block_time / 1e3))
                ORDER BY date
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


@AsyncTTL(time_to_live=5 * 60, maxsize=CACHE_MAX_SIZE)
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
