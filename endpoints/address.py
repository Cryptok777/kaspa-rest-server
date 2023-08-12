# encoding: utf-8
from typing import Any, List
import requests

from fastapi import Path, HTTPException, Query

from dbsession import async_session
from endpoints.models import (
    AddressInfoResponse,
    TransactionsResponse,
    TxInput,
    TxOutput,
)
from endpoints.stats import get_virtual_selected_parent_blue_score
from models.AddressBalancesRecord import AddressBalancesRecord
from models.AddressTag import AddressTag
from models.TxAddrMapping import TxAddrMapping
from server import app, kaspad_client

from pydantic import parse_obj_as
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy import text

from dbsession import async_session
from endpoints import filter_fields
from models.Block import Block
from models.Transaction import Transaction, TransactionOutput, TransactionInput
from sqlalchemy import func
from cache import AsyncTTL

MAX_VISIBLE_RANK = 1000


@AsyncTTL(time_to_live=60 * 60)
async def get_address_rank(address: str):
    sql = f"""
                WITH RankedAddresses AS (
                    SELECT  
                        address,
                        balance,
                        RANK() OVER (ORDER BY balance DESC) as rank
                    FROM address_balances
                    LIMIT :max_visible_rank
                )

                SELECT 
                    rank
                FROM RankedAddresses
                WHERE address = :address;
            """

    async with async_session() as session:
        resp = await session.execute(
            text(sql), {"address": address, "max_visible_rank": MAX_VISIBLE_RANK}
        )
        resp = resp.all()

    if len(resp) == 0:
        return None

    return resp[0][0]


@AsyncTTL(time_to_live=10 * 60)
async def get_addresses_tags(addresses: List[str]):
    async with async_session() as s:
        tags = await s.execute(
            select(AddressTag.address, AddressTag.name, AddressTag.link).where(
                AddressTag.address.in_(addresses)
            )
        )

    return [{"address": tag[0], "name": tag[1], "link": tag[2]} for tag in tags.all()]


@AsyncTTL(time_to_live=30 * 60)
async def get_addresses_balance_records(addresses: List[str], limit: int = 1):
    subquery = (
        select(
            AddressBalancesRecord.address,
            AddressBalancesRecord.balance,
            AddressBalancesRecord.created_at,
            func.row_number()
            .over(
                partition_by=AddressBalancesRecord.address,
                order_by=AddressBalancesRecord.created_at.desc(),
            )
            .label("row_num"),
        ).where(AddressBalancesRecord.address.in_(addresses))
    ).subquery()

    async with async_session() as s:
        records = await s.execute(
            select(subquery.c.address, subquery.c.balance, subquery.c.created_at).where(
                subquery.c.row_num <= limit
            )
        )

    records = records.all()
    records.reverse()

    return [
        {"address": record[0], "balance": record[1], "created_at": record[2]}
        for record in records
    ]


@AsyncTTL(time_to_live=10 * 60)
async def get_address_tags(address: str):
    async with async_session() as s:
        tags = await s.execute(
            select(AddressTag.name, AddressTag.link).filter(
                AddressTag.address == address
            )
        )

    tags = [{"name": tag[0], "link": tag[1]} for tag in tags.all()]

    rank = await get_address_rank(address=address)
    if rank:
        tags.append({"name": "#{}".format(rank), "type": "rank"})

    return tags


@AsyncTTL(time_to_live=3)
async def get_address_balance(address: str):
    """
    Get balance for a given kaspa address
    """
    resp = await kaspad_client.request(
        "getBalanceByAddressRequest", params={"address": address}
    )

    try:
        resp = resp["getBalanceByAddressResponse"]
    except KeyError:
        if (
            "getUtxosByAddressesResponse" in resp
            and "error" in resp["getUtxosByAddressesResponse"]
        ):
            raise HTTPException(
                status_code=400, detail=resp["getUtxosByAddressesResponse"]["error"]
            )
        else:
            raise

    try:
        balance = int(resp["balance"])

    # return 0 if address is ok, but no utxos there
    except KeyError:
        balance = 0

    return balance


@app.get(
    "/addresses/{kaspaAddress}/info",
    response_model=AddressInfoResponse,
    tags=["addresses"],
)
async def get_kaspa_address_info(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00",
    )
):
    """
    Get balance for a given kaspa address
    """
    balance = await get_address_balance(address=kaspaAddress)
    tags = await get_address_tags(address=kaspaAddress)
    balance_records = await get_addresses_balance_records(
        addresses=[kaspaAddress],
        limit=24 * 7,  # assuming job runs every hour, returns 7 days of data
    )

    return {
        "address": kaspaAddress,
        "balance": balance,
        "tags": tags,
        "balance_records": balance_records,
    }


@app.get(
    "/addresses/{kaspaAddress}/transactions",
    response_model=TransactionsResponse,
    response_model_exclude_unset=True,
    tags=["addresses"],
)
async def get_transactions_for_address(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. "
        "kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00",
    ),
    limit: int = Query(
        description="The number of records to get",
        ge=1,
        le=100,
        default=10,
    ),
    offset: int = Query(
        description="The offset from which to get records", ge=0, default=0
    ),
    fields: str = "",
):
    transactions = await get_transactions_for_address_local(
        kaspaAddress=kaspaAddress, limit=limit, offset=offset, fields=fields
    )
    transaction_count = await get_transaction_count_for_address(address=kaspaAddress)
    return TransactionsResponse(transactions=transactions, total=transaction_count)


async def get_transactions_for_address_local(
    kaspaAddress: str, limit: int, offset: int, fields: str = ""
):
    """
    Get all transactions for a given address from database
    """
    async with async_session() as s:
        # This query is slow with pagination
        await s.execute("SET LOCAL statement_timeout TO '10s';")

        # Doing it this way as opposed to adding it directly in the IN clause
        # so I can re-use the same result in tx_list, TxInput and TxOutput
        tx_within_limit_offset = await s.execute(
            select(TxAddrMapping.transaction_id)
            .filter(TxAddrMapping.address == kaspaAddress)
            .limit(limit)
            .offset(offset)
            .order_by(TxAddrMapping.block_time.desc())
        )

        tx_ids_in_page = [x[0] for x in tx_within_limit_offset.all()]

    return await search_for_transactions_local(
        transactionIds=tx_ids_in_page, fields=fields
    )


async def search_for_transactions_local(transactionIds: List[str], fields: str = ""):
    fields = fields.split(",") if fields else []

    async with async_session() as s:
        tx_list = await s.execute(
            select(Transaction, Block.blue_score)
            .join(Block, Transaction.accepting_block_hash == Block.hash, isouter=True)
            .filter(Transaction.transaction_id.in_(transactionIds))
            .order_by(Transaction.block_time.desc())
        )

        tx_list = tx_list.all()

        if not fields or "inputs" in fields:
            tx_inputs = await s.execute(
                select(TransactionInput).filter(
                    TransactionInput.transaction_id.in_(transactionIds)
                )
            )
            tx_inputs = tx_inputs.scalars().all()

            # Fetch input txns
            previous_outpoint_txns = await s.execute(
                select(TransactionOutput).where(
                    TransactionOutput.transaction_id.in_(
                        [tx_inp.previous_outpoint_hash for tx_inp in tx_inputs]
                    )
                )
            )

            previous_outpoint_txns = previous_outpoint_txns.scalars().all()
            previous_outpoint_txn_map = {}
            for tx in previous_outpoint_txns:
                if tx.transaction_id not in previous_outpoint_txn_map:
                    previous_outpoint_txn_map[tx.transaction_id] = {}
                previous_outpoint_txn_map[tx.transaction_id][tx.index] = tx
        else:
            tx_inputs = []

        if not fields or "outputs" in fields:
            tx_outputs = await s.execute(
                select(TransactionOutput).filter(
                    TransactionOutput.transaction_id.in_(transactionIds)
                )
            )
            tx_outputs = tx_outputs.scalars().all()
        else:
            tx_outputs = []

    blue_score = (await get_virtual_selected_parent_blue_score()).get("blueScore", 0)
    return list(
        (
            filter_fields(
                {
                    "subnetwork_id": tx.Transaction.subnetwork_id,
                    "transaction_id": tx.Transaction.transaction_id,
                    "hash": tx.Transaction.hash,
                    "mass": tx.Transaction.mass,
                    "block_hash": tx.Transaction.block_hash,
                    "block_time": tx.Transaction.block_time,
                    "is_accepted": tx.Transaction.is_accepted,
                    "confirmations": int(blue_score) - (tx.blue_score or 0),
                    "accepting_block_hash": tx.Transaction.accepting_block_hash,
                    "accepting_block_blue_score": tx.blue_score,
                    "outputs": parse_obj_as(
                        List[TxOutput],
                        [
                            x
                            for x in tx_outputs
                            if x.transaction_id == tx.Transaction.transaction_id
                        ],
                    ),
                    "inputs": parse_obj_as(
                        List[TxInput],
                        [
                            {
                                **x.__dict__,
                                "amount": previous_outpoint_txn_map[
                                    x.previous_outpoint_hash
                                ][x.previous_outpoint_index].amount,
                                "script_public_key_address": previous_outpoint_txn_map[
                                    x.previous_outpoint_hash
                                ][x.previous_outpoint_index].script_public_key_address,
                            }
                            for x in tx_inputs
                            if x.transaction_id == tx.Transaction.transaction_id
                            and previous_outpoint_txn_map.get(
                                x.previous_outpoint_hash, {}
                            ).get(x.previous_outpoint_index)
                        ],
                    ),
                },
                fields,
            )
            for tx in tx_list
        )
    )


async def get_transaction_count_for_address(address: str):
    """
    Count the number of transactions associated with this address
    """

    async with async_session() as s:
        count_query = select(func.count()).filter(TxAddrMapping.address == address)
        tx_count = await s.execute(count_query)

    return tx_count.scalar()


async def append_input_transactions_info(txs: list[dict[str, Any]]):
    if not txs:
        return txs

    # fetch address/amount for input tx
    pending_input_txs = []
    for tx in txs:
        for input_tx in tx.get("inputs", []):
            pending_input_txs.append(input_tx.previous_outpoint_hash)

    fetched_input_txs = await search_for_transactions_local(
        transactionIds=pending_input_txs, fields="outputs"
    )

    # convert to map[tx_id][index] = {amount, address}
    tx_map = {}
    for tx in fetched_input_txs:
        for output_tx in tx.get("outputs", []):
            tx_id = output_tx.transaction_id
            index = output_tx.index
            address = output_tx.script_public_key_address
            amount = output_tx.amount
            tx_map[tx_id] = tx_map.get(tx_id, {})
            tx_map[tx_id][index] = {
                "amount": amount,
                "script_public_key_address": address,
            }

    # Insert amount/address back to final payload
    for tx in txs:
        for input_tx in tx.get("inputs", []):
            tx_id = input_tx.previous_outpoint_hash
            index = input_tx.previous_outpoint_index
            target_tx_from_map = tx_map.get(tx_id, {}).get(index, {})

            input_tx.amount = target_tx_from_map.get("amount", 0)
            input_tx.script_public_key_address = target_tx_from_map.get(
                "script_public_key_address"
            )

    # sort txs by block_time
    return sorted(txs, key=lambda x: x["block_time"], reverse=True)
