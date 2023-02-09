# encoding: utf-8
from typing import Any, List
import requests

from fastapi import Path, HTTPException, Query
from sqlalchemy import text

from dbsession import async_session
from endpoints.models import TxInput, TxModel, TxOutput
from server import app, kaspad_client
from datetime import datetime

from pydantic import BaseModel, parse_obj_as
from sqlalchemy.future import select

from dbsession import async_session
from endpoints import filter_fields
from models.Block import Block
from models.Transaction import Transaction, TransactionOutput, TransactionInput

PRECISION = 1e8


class AddressInfoTag(BaseModel):
    name: str
    reference: str


class AddressInfoResponse(BaseModel):
    address: str = "kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00"
    balance: int = 38240000000
    tag: AddressInfoTag


@app.get(
    "/addresses/{kaspaAddress}/info",
    response_model=AddressInfoResponse,
    tags=["addresses"],
)
async def get_kaspa_address_info(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00",
        regex="^kaspa\:[a-z0-9]{61}$",
    )
):
    """
    Get balance for a given kaspa address
    """
    resp = await kaspad_client.request(
        "getBalanceByAddressRequest", params={"address": kaspaAddress}
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

    return {
        "address": kaspaAddress,
        "balance": balance,
        "tag": {"name": "Block explorer", "reference": "https://google.ca"},
    }


@app.get(
    "/addresses/{kaspaAddress}/transactions",
    response_model=List[TxModel],
    response_model_exclude_unset=True,
    tags=["addresses"],
)
async def get_transactions_for_address(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. "
        "kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00",
        regex="^kaspa\:[a-z0-9]{61}$",
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
):
    return await get_transactions_for_address_remote(
        kaspaAddress=kaspaAddress, limit=limit, offset=offset
    )


async def append_input_transcations_info(txs: list[dict[str, Any]]):
    if not txs:
        return txs

    # fetch address/amount for input tx
    pending_input_txs = []
    for tx in txs:
        for input_tx in tx.get("inputs", []):
            pending_input_txs.append(input_tx.previous_outpoint_hash)

    fetched_input_txs = search_for_transactions_remote(
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


async def get_transactions_for_address_local(
    kaspaAddress: str,
    limit: int,
    offset: int,
):
    """
    Get all transactions for a given address from database
    """
    async with async_session() as session:
        resp = await session.execute(
            text(
                f"""
            SELECT transactions_outputs.transaction_id, transactions_outputs.index, transactions_inputs.transaction_id as inp_transaction,
                    transactions.block_time, transactions.transaction_id
            
            FROM transactions

			LEFT JOIN transactions_outputs ON transactions.transaction_id = transactions_outputs.transaction_id
			LEFT JOIN transactions_inputs ON transactions_inputs.previous_outpoint_hash = transactions.transaction_id AND transactions_inputs.previous_outpoint_index::int = transactions_outputs.index

            WHERE "script_public_key_address" = '{kaspaAddress}'
			ORDER by transactions.block_time DESC
            LIMIT {limit}
            OFFSET {offset}
            """
            )
        )

        resp = resp.all()

    tx_list = []
    for x in resp:
        tx_list.append(x[0])
        tx_list.append(x[2])

    tx_list = list(filter(lambda x: x != None, tx_list))
    txs = await search_for_transactions_local(transactionIds=tx_list)

    return await append_input_transcations_info(txs)


async def get_transactions_for_address_remote(
    kaspaAddress: str,
    limit: int,
    offset: int,
):
    resp = requests.get(
        f"https://api.kaspa.org/addresses/{kaspaAddress}/full-transactions?limit={limit}&offset={offset}",
    )
    if resp.status_code == 200:
        resp = resp.json()
        for tx in resp:
            tx["inputs"] = parse_obj_as(List[TxInput], tx["inputs"])
            tx["outputs"] = parse_obj_as(List[TxOutput], tx["outputs"])
        return await append_input_transcations_info(resp)

    return []


async def search_for_transactions_local(transactionIds: List[str], fields: str = ""):
    fields = fields.split(",") if fields else []

    async with async_session() as s:
        tx_list = await s.execute(
            select(Transaction, Block.blue_score)
            .join(Block, Transaction.accepting_block_hash == Block.hash)
            .filter(Transaction.transaction_id.in_(transactionIds))
        )

        tx_list = tx_list.all()

        if not fields or "inputs" in fields:
            tx_inputs = await s.execute(
                select(TransactionInput).filter(
                    TransactionInput.transaction_id.in_(transactionIds)
                )
            )
            tx_inputs = tx_inputs.scalars().all()
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
                            x
                            for x in tx_inputs
                            if x.transaction_id == tx.Transaction.transaction_id
                        ],
                    ),
                },
                fields,
            )
            for tx in tx_list
        )
    )


def search_for_transactions_remote(transactionIds: List[str], fields: str = ""):
    resp = requests.post(
        "https://api.kaspa.org/transactions/search",
        json={"transactionIds": transactionIds},
    )
    if resp.status_code == 200:
        resp = resp.json()
        for tx in resp:
            tx["inputs"] = parse_obj_as(List[TxInput], tx["inputs"] or [])
            tx["outputs"] = parse_obj_as(List[TxOutput], tx["outputs"])
        return resp

    return []
