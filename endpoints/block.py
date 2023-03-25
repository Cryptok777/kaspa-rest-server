# encoding: utf-8
from typing import List

from fastapi import Query, Path, HTTPException
from fastapi import Response
from pydantic import BaseModel
from sqlalchemy import select

from dbsession import async_session
from endpoints.models import BlockModel, BlockResponse
from endpoints.stats import get_virtual_selected_parent_blue_score
from endpoints.utils import camel_to_snake_case_deep, kaspadBlockToModel
from models.Block import Block
from models.Transaction import Transaction, TransactionOutput, TransactionInput
from server import app, kaspad_client
from sqlalchemy.dialects.postgresql import ARRAY


@app.get("/blocks/{blockId}", response_model=BlockModel, tags=["blocks"])
async def get_block(response: Response, blockId: str = Path(regex="[a-f0-9]{64}")):
    """
    Get block information for a given block id
    """
    resp = await kaspad_client.request(
        "getBlockRequest", params={"hash": blockId, "includeTransactions": True}
    )
    requested_block = None

    if "block" in resp["getBlockResponse"]:
        # We found the block in kaspad. Just use it
        requested_block = kaspadBlockToModel(resp["getBlockResponse"]["block"])
        response.headers["X-Data-Source"] = "Kaspad"
    else:
        # Didn't find the block in kaspad. Try getting it from the DB
        response.headers["X-Data-Source"] = "Database"
        requested_block = await get_block_from_db(blockId)

    if not requested_block:
        # Still did not get the block
        raise HTTPException(status_code=404, detail="Block not found")

    # We found the block, now we guarantee it contains the transactions
    # It's possible that the block from kaspad does not contain transactions
    if "transactions" not in requested_block or not requested_block["transactions"]:
        blue_score = requested_block.get("header", {}).get("blue_score")
        requested_block["transactions"] = await get_block_transactions(
            blockId, int(blue_score)
        )

    return requested_block


@app.get("/blocks", response_model=BlockResponse, tags=["blocks"])
async def get_blocks(
    lowHash: str = Query(regex="[a-f0-9]{64}"),
    includeBlocks: bool = False,
    includeTransactions: bool = False,
):
    """
    Lists block beginning from a low hash (block id). Note that this function is running on a kaspad and not returning
    data from database.
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


"""
Get the block from the database
"""


async def get_block_from_db(blockId):
    async with async_session() as s:
        requested_block = await s.execute(
            select(Block).where(Block.hash == blockId).limit(1)
        )

        try:
            requested_block = requested_block.first()[0]  # type: Block
        except TypeError:
            raise HTTPException(status_code=404, detail="Block not found")

    if requested_block:
        return {
            "header": {
                "version": requested_block.version,
                "hash_merkle_root": requested_block.hash_merkle_root,
                "accepted_id_merkle_root": requested_block.accepted_id_merkle_root,
                "utxo_commitment": requested_block.utxo_commitment,
                "timestamp": round(requested_block.timestamp.timestamp() * 1000),
                "bits": requested_block.bits,
                "nonce": requested_block.nonce,
                "daa_score": requested_block.daa_score,
                "blue_work": requested_block.blue_work,
                "parents": [{"parent_hashes": requested_block.parents}],
                "blue_score": requested_block.blue_score,
                "pruning_point": requested_block.pruning_point,
            },
            "transactions": None,  # this will be filled later
            "verbose_data": {
                "hash": requested_block.hash,
                "difficulty": requested_block.difficulty,
                "selected_parent_hash": requested_block.selected_parent_hash,
                "transaction_ids": [],
                "blue_score": requested_block.blue_score,
                "children_hashes": [],
                "merge_set_blues_hashes": requested_block.merge_set_blues_hashes,
                "merge_set_reds_hashes": requested_block.merge_set_reds_hashes,
                "is_chain_block": requested_block.is_chain_block,
            },
        }
    return None


"""
Get the transactions associated with a block
"""


async def get_block_transactions(blockId, block_blue_score):
    # create tx data
    tx_list = []
    blue_score = (await get_virtual_selected_parent_blue_score()).get("blueScore", 0)

    async with async_session() as s:
        transactions = await s.execute(
            select(Transaction).filter(Transaction.block_hash.contains([blockId]))
        )

        transactions = transactions.scalars().all()

        tx_outputs = await s.execute(
            select(TransactionOutput).where(
                TransactionOutput.transaction_id.in_(
                    [tx.transaction_id for tx in transactions]
                )
            )
        )

        tx_outputs = tx_outputs.scalars().all()

        tx_inputs = await s.execute(
            select(TransactionInput).where(
                TransactionInput.transaction_id.in_(
                    [tx.transaction_id for tx in transactions]
                )
            )
        )

        tx_inputs = tx_inputs.scalars().all()

        # Fetch input address
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

    confirmations = int(blue_score) - (block_blue_score or 0)
    for tx in transactions:
        tx_list.append(
            {
                "inputs": [
                    {
                        "transaction_id": tx.transaction_id,
                        "index": tx_inp.index,
                        "previous_outpoint_hash": tx_inp.previous_outpoint_hash,
                        "previous_outpoint_index": tx_inp.previous_outpoint_index,
                        "signature_script": tx_inp.signature_script,
                        "amount": previous_outpoint_txn_map[
                            tx_inp.previous_outpoint_hash
                        ][tx_inp.previous_outpoint_index].amount,
                        "script_public_key_address": previous_outpoint_txn_map[
                            tx_inp.previous_outpoint_hash
                        ][tx_inp.previous_outpoint_index].script_public_key_address,
                    }
                    for tx_inp in tx_inputs
                    if tx_inp.transaction_id == tx.transaction_id
                    and previous_outpoint_txn_map.get(
                        tx_inp.previous_outpoint_hash, {}
                    ).get(tx_inp.previous_outpoint_index)
                ],
                "outputs": [
                    {
                        "transaction_id": tx.transaction_id,
                        "amount": tx_out.amount,
                        "index": tx_out.index,
                        "script_public_key": tx_out.script_public_key,
                        "script_public_key_type": tx_out.script_public_key_type,
                        "script_public_key_address": tx_out.script_public_key_address,
                    }
                    for tx_out in tx_outputs
                    if tx_out.transaction_id == tx.transaction_id
                ],
                "subnetwork_id": tx.subnetwork_id,
                "transaction_id": tx.transaction_id,
                "hash": tx.hash,
                "mass": tx.mass,
                "block_hash": tx.block_hash,
                "block_time": tx.block_time,
                "is_accepted": tx.is_accepted,
                "confirmations": confirmations,
            }
        )

    return tx_list
