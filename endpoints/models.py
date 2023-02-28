from typing import List

from pydantic import BaseModel


class BlockdagResponse(BaseModel):
    networkName: str
    blockCount: str
    headerCount: str
    tipHashes: List[str]
    difficulty: float
    pastMedianTime: str
    virtualParentHashes: List[str]
    pruningPointHash: str
    virtualDaaScore: str


class BlockRewardResponse(BaseModel):
    blockreward: float


class HalvingResponse(BaseModel):
    nextHalvingTimestamp: int
    nextHalvingDate: str
    nextHalvingAmount: float


class NetworkResponse(BaseModel):
    networkName: str
    blockCount: str
    headerCount: str
    tipHashes: List[str]
    difficulty: float
    pastMedianTime: str
    virtualParentHashes: List[str]
    pruningPointHash: str
    virtualDaaScore: str


class BlockdagResponse(BaseModel):
    blueScore: int


class KaspadResponse(BaseModel):
    kaspadHost: str
    serverVersion: str
    isUtxoIndexed: bool
    isSynced: bool
    p2pId: str


class HealthResponse(BaseModel):
    kaspadServers: List[KaspadResponse]


class CoinSupplyResponse(BaseModel):
    circulatingSupply: str
    maxSupply: str


class HashrateResponse(BaseModel):
    hashrate: float


class KaspadInfoResponse(BaseModel):
    mempoolSize: str
    serverVersion: str
    isUtxoIndexed: bool
    isSynced: bool
    p2pIdHashed: str


# Dashboard API


class DashboardMetricsResponse(BaseModel):
    block_count: int
    daa_score: int
    tps: float
    current_supply: int
    hashrate: float
    mined_pct: float
    next_halving_timestamp: int
    next_halving_reward: float


class MarketResponse(BaseModel):
    cmc_rank: int
    price: float
    price_pct_change_24h: float
    volume_24h: int
    market_cap: int


class WhaleMovement(BaseModel):
    transaction_id: str
    time: int
    amount: float
    receiver: str


class WhaleMovementResponse(BaseModel):
    transactions: List[WhaleMovement]


class GraphResponse(BaseModel):
    x: str | int
    y: int


class GraphsResponse(BaseModel):
    active_address: List[GraphResponse]
    tx_count: List[GraphResponse]


class SearchResponse(BaseModel):
    result_type: str
    value: str


class TxInput(BaseModel):
    transaction_id: str
    index: int
    previous_outpoint_hash: str
    previous_outpoint_index: int
    signature_script: str
    amount: int | None
    script_public_key_address: str | None

    class Config:
        orm_mode = True


class TxOutput(BaseModel):
    transaction_id: str
    index: int
    amount: int
    script_public_key: str
    script_public_key_address: str
    script_public_key_type: str
    accepting_block_hash: str | None

    class Config:
        orm_mode = True


class TxModel(BaseModel):
    subnetwork_id: str | None
    transaction_id: str | None
    hash: str | None
    mass: str | None
    block_hash: List[str] | None
    block_time: int | None
    is_accepted: bool | None
    accepting_block_hash: str | None
    accepting_block_blue_score: int | None
    inputs: List[TxInput] | None
    outputs: List[TxOutput] | None

    class Config:
        orm_mode = True


class VerboseDataModel(BaseModel):
    hash: str = "18c7afdf8f447ca06adb8b4946dc45f5feb1188c7d177da6094dfbc760eca699"
    difficulty: float = (4102204523252.94,)
    selected_parent_hash: str = (
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    )
    transaction_ids: list[str] = [
        "533f8314bf772259fe517f53507a79ebe61c8c6a11748d93a0835551233b3311"
    ]
    blue_score: str = "18483232"
    children_hashes: list[str] = [
        "2fda0dad4ec879b4ad02ebb68c757955cab305558998129a7de111ab852e7dcb",
        "9a822351cd293a653f6721afec1646bd1690da7124b5fbe87001711406010604",
    ]
    merge_set_blues_hashes: list[str] = [
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    ]
    merge_set_reds_hashes: list[str] = [
        "580f65c8da9d436480817f6bd7c13eecd9223b37f0d34ae42fb17e1e9fda397e"
    ]
    is_chain_block: bool = False


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

class BlockTranscationModel(BaseModel):
    inputs: None
    outputs: None
    subnetworkId:  None
    verboseData: None

class BlockModel(BaseModel):
    header: BlockHeader
    transactions: List[TxModel] | None
    verbose_data: VerboseDataModel


class BlockResponse(BaseModel):
    blockHashes: List[str] = []
    blocks: List[BlockModel] | None
