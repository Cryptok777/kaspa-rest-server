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
    date: str
    count: int


class GraphsResponse(BaseModel):
    active_address: List[GraphResponse]
    tx_count: List[GraphResponse]


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
