from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class AddressInfoTag(BaseModel):
    address: str | None
    name: str
    link: str | None
    type: str | None


class AddressBalanceRecord(BaseModel):
    address: str
    balance: int
    created_at: datetime


class AddressInfoResponse(BaseModel):
    address: str
    balance: int
    tags: List[AddressInfoTag]
    balance_records: List[AddressBalanceRecord]


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
    max_tps: float
    bps: float
    current_supply: int
    hashrate: float
    max_hashrate: float
    mined_pct: float
    current_reward: float
    next_halving_timestamp: int
    next_halving_reward: float
    header_count: int
    current_addresses_count: int


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
    confirmations: int | None

    class Config:
        orm_mode = True


class TransactionsResponse(BaseModel):
    transactions: List[TxModel]
    total: int


class VerboseDataModel(BaseModel):
    hash: str
    difficulty: float
    selected_parent_hash: str
    blue_score: str
    children_hashes: list[str]
    is_chain_block: bool = False


class ParentHashModel(BaseModel):
    parent_hashes: List[str]


class BlockHeader(BaseModel):
    version: int = 1
    hash_merkle_root: str
    accepted_id_merkle_root: str
    utxo_commitment: str
    timestamp: str
    bits: int
    nonce: str
    daa_score: str
    blue_work: str
    parents: list[ParentHashModel]
    blue_score: str
    pruning_point: str


class BlockTransactionModel(BaseModel):
    inputs: None
    outputs: None
    subnetworkId: None
    verboseData: None


class BlockModel(BaseModel):
    header: BlockHeader
    transactions: List[TxModel] | None
    verbose_data: VerboseDataModel


class BlockResponse(BaseModel):
    blockHashes: List[str] = []
    blocks: List[BlockModel] | None


class HoldersOverviewResponse(BaseModel):
    holders_count: int
    top_10_holder: float
    top_50_holder: float
    top_100_holder: float
    top_500_holder: float
    top_1000_holder: float


class HolderModel(BaseModel):
    address: str
    balance: int
    percentage: float
    tags: List[AddressInfoTag] | None


class HoldersListResponse(BaseModel):
    holders: List[HolderModel]


class DistributionTrendCategory(BaseModel):
    count: int
    change_24h: float | None
    change_7d: float | None
    change_30d: float | None


class DistributionTrendResponse(BaseModel):
    timestamp: int
    addresses_in_1e2: DistributionTrendCategory
    addresses_in_1e3: DistributionTrendCategory
    addresses_in_1e4: DistributionTrendCategory
    addresses_in_1e5: DistributionTrendCategory
    addresses_in_1e6: DistributionTrendCategory
    addresses_in_1e7: DistributionTrendCategory
    addresses_in_1e8: DistributionTrendCategory
    addresses_in_1e9: DistributionTrendCategory
    addresses_in_1e10: DistributionTrendCategory


class DistributionTrendChartResponse(BaseModel):
    chartData: List[DistributionTrendResponse]
