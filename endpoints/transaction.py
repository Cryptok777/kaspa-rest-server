# encoding: utf-8
from typing import List
import requests

from fastapi import Path, HTTPException
from pydantic import parse_obj_as
from sqlalchemy.future import select

from dbsession import async_session
from endpoints.address import append_input_transactions_info
from endpoints.models import TxInput, TxModel, TxOutput
from models.Block import Block
from models.Transaction import Transaction, TransactionOutput, TransactionInput
from server import app


async def _get_transaction_local(
    transactionId: str = Path(regex="[a-f0-9]{64}"),
    inputs: bool = True,
    outputs: bool = True,
):
    """
    Get tx information for a given tx id
    """
    async with async_session() as s:
        tx = await s.execute(
            select(Transaction, Block.blue_score)
            .join(Block, Transaction.accepting_block_hash == Block.hash, isouter=True)
            .filter(Transaction.transaction_id == transactionId)
        )

        tx = tx.first()

        tx_outputs = None
        tx_inputs = None

        if outputs:
            tx_outputs = await s.execute(
                select(TransactionOutput).filter(
                    TransactionOutput.transaction_id == transactionId
                )
            )

            tx_outputs = tx_outputs.scalars().all()

        if inputs:
            tx_inputs = await s.execute(
                select(TransactionInput).filter(
                    TransactionInput.transaction_id == transactionId
                )
            )
            tx_inputs = tx_inputs.scalars().all()

    if tx:
        tx = {
            "subnetwork_id": tx.Transaction.subnetwork_id,
            "transaction_id": tx.Transaction.transaction_id,
            "hash": tx.Transaction.hash,
            "mass": tx.Transaction.mass,
            "block_hash": tx.Transaction.block_hash,
            "block_time": tx.Transaction.block_time,
            "is_accepted": tx.Transaction.is_accepted,
            "accepting_block_hash": tx.Transaction.accepting_block_hash,
            "accepting_block_blue_score": tx.blue_score,
            "outputs": parse_obj_as(List[TxOutput], tx_outputs) if tx_outputs else [],
            "inputs": parse_obj_as(List[TxInput], tx_inputs) if tx_inputs else [],
        }
        return (await append_input_transactions_info([tx]))[0]
    else:
        raise HTTPException(status_code=404, detail="Transaction not found")


@app.get(
    "/transactions/{transactionId}",
    response_model=TxModel,
    tags=["Kaspa transactions"],
    response_model_exclude_unset=True,
)
async def get_transaction(
    transactionId: str = Path(regex="[a-f0-9]{64}"),
    inputs: bool = True,
    outputs: bool = True,
):
    return await _get_transaction_local(
        transactionId=transactionId, inputs=inputs, outputs=outputs
    )
