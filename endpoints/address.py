# encoding: utf-8
from typing import List

from fastapi import Path, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from dbsession import async_session
from server import app, kaspad_client


class BalanceResponse(BaseModel):
    address: str = "kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00"
    balance: int = 38240000000


@app.get(
    "/addresses/{kaspaAddress}/balance",
    response_model=BalanceResponse,
    tags=["Kaspa addresses"],
)
async def get_balance_from_kaspa_address(
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

    return {"address": kaspaAddress, "balance": balance}


class TransactionsReceivedAndSpent(BaseModel):
    tx_received: str
    tx_spent: str | None


class TransactionForAddressResponse(BaseModel):
    transactions: List[TransactionsReceivedAndSpent]


@app.get(
    "/addresses/{kaspaAddress}/transactions",
    response_model=TransactionForAddressResponse,
    response_model_exclude_unset=True,
    tags=["Kaspa addresses"],
)
async def get_transactions_for_address(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. "
        "kaspa:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00",
        regex="^kaspa\:[a-z0-9]{61}$",
    )
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
			LIMIT 500"""
            )
        )

        resp = resp.all()

    # build response
    tx_list = []
    for x in resp:
        tx_list.append({"tx_received": x[0], "tx_spent": x[2]})
    return {"transactions": tx_list}


class OutpointModel(BaseModel):
    transactionId: str = (
        "ef62efbc2825d3ef9ec1cf9b80506876ac077b64b11a39c8ef5e028415444dc9"
    )
    index: int = 0


class ScriptPublicKeyModel(BaseModel):
    scriptPublicKey: str = (
        "20c5629ce85f6618cd3ed1ac1c99dc6d3064ed244013555c51385d9efab0d0072fac"
    )


class UtxoModel(BaseModel):
    amount: str = ("11501593788",)
    scriptPublicKey: ScriptPublicKeyModel
    blockDaaScore: str = "18867232"


class UtxoResponse(BaseModel):
    address: str = "kaspa:qrzk988gtanp3nf76xkpexwud5cxfmfygqf42hz38pwea74s6qrj75jee85nj"
    outpoint: OutpointModel
    utxoEntry: UtxoModel


@app.get(
    "/addresses/{kaspaAddress}/utxos",
    response_model=List[UtxoResponse],
    tags=["Kaspa addresses"],
)
async def get_utxos_for_address(
    kaspaAddress: str = Path(
        description="Kaspa address as string e.g. kaspa:qqkqkzjvr7zwxxmjxjkmxxdwju9kjs6e9u82uh59z07vgaks6gg62v8707g73",
        regex="^kaspa\:[a-z0-9]{61}$",
    )
):
    """
    Lists all open utxo for a given kaspa address
    """
    resp = await kaspad_client.request(
        "getUtxosByAddressesRequest", params={"addresses": [kaspaAddress]}, timeout=120
    )
    try:
        return (
            utxo
            for utxo in resp["getUtxosByAddressesResponse"]["entries"]
            if utxo["address"] == kaspaAddress
        )
    except KeyError:
        if (
            "getUtxosByAddressesResponse" in resp
            and "error" in resp["getUtxosByAddressesResponse"]
        ):
            raise HTTPException(
                status_code=400, detail=resp["getUtxosByAddressesResponse"]["error"]
            )
        raise
