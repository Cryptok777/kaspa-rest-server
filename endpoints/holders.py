# encoding: utf-8


from endpoints.address import get_addresses_tags
from endpoints.models import HoldersListResponse, HoldersOverviewResponse

from sqlalchemy import select
from sqlalchemy import text

from dbsession import async_session
from endpoints.stats import get_coinsupply
from models.AddressBalance import AddressBalance
from server import app
from sqlalchemy import func
from cache import AsyncTTL


@AsyncTTL(time_to_live=60 * 60)
async def get_total_holders():
    async with async_session() as s:
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
        top_100_holder=sum(address["balance"] for address in addresses)
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
    address_tag_map = {}
    for tag in addresses_tags:
        address_tag_map[tag["address"]] = address_tag_map.get(tag["address"], [])
        address_tag_map[tag["address"]].append(tag)

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
