# encoding: utf-8
from typing import List

from fastapi import Query, Path, HTTPException
from pydantic import BaseModel

from server import app, kaspad_client


class VerboseDataModel(BaseModel):
    hash: str = "18c7afdf8f447ca06adb8b4946dc45f5feb1188c7d177da6094dfbc760eca699"
    difficulty: float = (4102204523252.94,)
    selectedParentHash: str = (
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    )
    transactionIds: List[str] = [
        "533f8314bf772259fe517f53507a79ebe61c8c6a11748d93a0835551233b3311"
    ]
    blueScore: str = "18483232"
    childrenHashes: List[str] = [
        "2fda0dad4ec879b4ad02ebb68c757955cab305558998129a7de111ab852e7dcb",
        "9a822351cd293a653f6721afec1646bd1690da7124b5fbe87001711406010604",
    ]
    mergeSetBluesHashes: List[str] = [
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    ]
    mergeSetRedsHashes: List[str] = [
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    ]
    isChainBlock: bool = False


class ParentHashModel(BaseModel):
    parentHashes: List[str] = [
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    ]


class BlockHeader(BaseModel):
    version: int = 1
    hashMerkleRoot: str = (
        "e6641454e16cff4f232b899564eeaa6e480b66069d87bee6a2b2476e63fcd887"
    )
    acceptedIdMerkleRoot: str = (
        "9bab45b027a0b2b47135b6f6f866e5e4040fc1fdf2fe56eb0c90a603ce86092b"
    )
    utxoCommitment: str = (
        "236d5f9ffd19b317a97693322c3e2ae11a44b5df803d71f1ccf6c2393bc6143c"
    )
    timestamp: str = "1656450648874"
    bits: int = 455233226
    nonce: str = "14797571275553019490"
    daaScore: str = "19984482"
    blueWork: str = "2d1b3f04f8a0dcd31"
    parents: List[ParentHashModel]
    blueScore: str = "18483232"
    pruningPoint: str = (
        "5d32a9403273a34b6551b84340a1459ddde2ae6ba59a47987a6374340ba41d5d"
    )


class BlockModel(BaseModel):
    header: BlockHeader
    transactions: list | None
    verboseData: VerboseDataModel


class BlockResponse(BaseModel):
    blockHashes: List[str] = [
        "44edf9bfd32aa154bfad64485882f184372b64bd60565ba121b42fc3cb1238f3",
        "18c7afdf8f447ca06adb8b4946dc45f5feb1188c7d177da6094dfbc760eca699",
        "9a822351cd293a653f6721afec1646bd1690da7124b5fbe87001711406010604",
        "2fda0dad4ec879b4ad02ebb68c757955cab305558998129a7de111ab852e7dcb",
    ]
    blocks: List[BlockModel] | None


@app.get("/blocks/{blockId}", response_model=BlockModel, tags=["Kaspa blocks"])
async def get_block(blockId: str = Path(regex="[a-f0-9]{64}")):
    """
    Get block information for a given block id
    """
    resp = await kaspad_client.request(
        "getBlockRequest", params={"hash": blockId, "includeTransactions": True}
    )
    try:
        return resp["getBlockResponse"]["block"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Block not found")


@app.get("/blocks", response_model=BlockResponse, tags=["Kaspa blocks"])
async def get_blocks(
    lowHash: str = Query(regex="[a-f0-9]{64}"),
    includeBlocks: bool = False,
    includeTransactions: bool = False,
):
    """
    Lists block beginning from a low hash (block id)
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
