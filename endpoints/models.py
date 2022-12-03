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