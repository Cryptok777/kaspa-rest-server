# encoding: utf-8


from endpoints.address import get_addresses_balance_records, get_addresses_tags
from endpoints.models import (
    DistributionTrendCategory,
    HoldersListResponse,
    HoldersOverviewResponse,
    DistributionTrendChartResponse,
)

from sqlalchemy import select
from sqlalchemy import text

from dbsession import async_session
from endpoints.stats import get_coinsupply
from models.AddressBalance import AddressBalance
from server import app
from sqlalchemy import func
from cache import AsyncTTL

import calendar


@AsyncTTL(time_to_live=60 * 60)
async def get_total_holders():
    async with async_session() as s:
        await s.execute("SET LOCAL statement_timeout TO '10s';")

        count_query = select(func.count()).filter(AddressBalance.balance > 0)
        tx_count = await s.execute(count_query)

    return tx_count.scalar()


@app.get("/holders/overview", response_model=HoldersOverviewResponse, tags=["holders"])
async def get_holders_overview():
    sql = f"""
                SELECT  
                    address
                    ,balance
                FROM agg_top_holders
                ORDER BY balance DESC
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    addresses = []
    for x in resp:
        addresses.append(
            {
                "address": x[0],
                "balance": float(x[1]),
            }
        )

    current_supply = float((await get_coinsupply())["circulatingSupply"])
    total_holders = await get_total_holders()

    return HoldersOverviewResponse(
        holders_count=total_holders,
        top_1000_holder=sum(address["balance"] for address in addresses[:1000])
        / current_supply
        * 100,
        top_500_holder=sum(address["balance"] for address in addresses[:500])
        / current_supply
        * 100,
        top_100_holder=sum(address["balance"] for address in addresses[:100])
        / current_supply
        * 100,
        top_50_holder=sum(address["balance"] for address in addresses[:50])
        / current_supply
        * 100,
        top_20_holder=sum(address["balance"] for address in addresses[:20])
        / current_supply
        * 100,
        top_10_holder=sum(address["balance"] for address in addresses[:10])
        / current_supply
        * 100,
    )


@app.get("/holders/list", response_model=HoldersListResponse, tags=["holders"])
async def get_holders_list():
    sql = f"""
                SELECT  
                    address
                    ,balance
                FROM agg_top_holders
                ORDER BY balance DESC
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    addresses = []
    for x in resp:
        addresses.append(
            {
                "address": x[0],
                "balance": float(x[1]),
            }
        )

    addresses_tags = await get_addresses_tags([i["address"] for i in addresses])
    addresse_balance_records = await get_addresses_balance_records(
        [i["address"] for i in addresses]
    )

    # get a map of address -> balance records
    balance_record_map = {}
    for record in addresse_balance_records:
        balance_record_map[record["address"]] = balance_record_map.get(
            record["address"], True
        )

    # get a map of address -> tags
    address_tag_map = {}
    for tag in addresses_tags:
        address_tag_map[tag["address"]] = address_tag_map.get(tag["address"], [])
        address_tag_map[tag["address"]].append(tag)
        # Add a tag for history available
        if balance_record_map.get(tag["address"]):
            address_tag_map[tag["address"]].append(
                {
                    "address": tag["address"],
                    "name": "History Available",
                }
            )

    current_supply = float((await get_coinsupply())["circulatingSupply"])

    return HoldersListResponse(
        holders=[
            {
                **address,
                "percentage": address["balance"] / current_supply * 100,
                "tags": address_tag_map.get(address["address"]),
            }
            for address in addresses
        ]
    )


def get_pct_change(prev, now):
    if prev != 0:
        return ((now - prev) / prev) * 100
    elif prev == 0 and now > 0:
        return 100
    else:
        return 0


@AsyncTTL(time_to_live=30 * 60)
async def _get_distribution_trend_chart():
    columns = [f"addresses_in_1e{i}" for i in range(2, 11)]
    sql = f"""
                SELECT 
                     {",".join(columns)}
                    ,created_at
                FROM agg_address_statistics
                WHERE created_at > current_date - interval '90' day
                ORDER BY created_at ASC;
            """

    async with async_session() as session:
        resp = await session.execute(text(sql))
        resp = resp.all()

    chart_data = []
    for row_index, row in enumerate(resp):
        row_data = {}
        for index in range(len(columns)):
            # Only calculate the percentage for the last row
            if row_index == len(resp) - 1:
                # Assume the data interval is 1 hour
                row_from_24h_ago = resp[row_index - 24]
                row_from_7d_ago = resp[row_index - 24 * 7]
                row_from_30d_ago = resp[row_index - 24 * 30]

                row_data[columns[index]] = DistributionTrendCategory(
                    count=row[index],
                    change_24h=get_pct_change(row_from_24h_ago[index], row[index]),
                    change_7d=get_pct_change(row_from_7d_ago[index], row[index]),
                    change_30d=get_pct_change(row_from_30d_ago[index], row[index]),
                )
            else:
                row_data[columns[index]] = DistributionTrendCategory(count=row[index])

        row_data["timestamp"] = calendar.timegm(row[index + 1].utctimetuple())
        chart_data.append(row_data)

    return {"chartData": chart_data}


@app.get(
    "/holders/distribution_trend",
    response_model=DistributionTrendChartResponse,
    tags=["holders"],
)
async def get_distribution_trend_chart():
    return await _get_distribution_trend_chart()
