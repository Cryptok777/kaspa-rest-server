from typing import List

from pydantic import BaseModel


class BlockdagResponse(BaseModel):
    networkName: str = "kaspa-mainnet"
    blockCount: str = "260890"
    headerCount: str = "2131312"
    tipHashes: List[str] = [
        "78273854a739e3e379dfd34a262bbe922400d8e360e30e3f31228519a334350a"
    ]
    difficulty: float = 3870677677777.2
    pastMedianTime: str = "1656455670700"
    virtualParentHashes: List[str] = [
        "78273854a739e3e379dfd34a262bbe922400d8e360e30e3f31228519a334350a"
    ]
    pruningPointHash: str = (
        "5d32a9403273a34b6551b84340a1459ddde2ae6ba59a47987a6374340ba41d5d",
    )
    virtualDaaScore: str = "19989141"


class BlockRewardResponse(BaseModel):
    blockreward: float = 12000132


class HalvingResponse(BaseModel):
    nextHalvingTimestamp: int = 1662837270000
    nextHalvingDate: str = "2022-09-10 19:38:52 UTC"
    nextHalvingAmount: float = 155.123123


class NetworkResponse(BaseModel):
    networkName: str = "kaspa-mainnet"
    blockCount: str = "261357"
    headerCount: str = "23138783"
    tipHashes: List[str] = [
        "efdbe104c6275cf881583fba77834c8528fd1ab059f6b4737c42564d0d9fedbc",
        "6affbe62baef0f1a562f166b9857844b03b51a8ec9b8417ceb308d53fdc239a2",
    ]
    difficulty: float = 3887079905014.09
    pastMedianTime: str = "1656456088196"
    virtualParentHashes: List[str] = [
        "6affbe62baef0f1a562f166b9857844b03b51a8ec9b8417ceb308d53fdc239a2",
        "efdbe104c6275cf881583fba77834c8528fd1ab059f6b4737c42564d0d9fedbc",
    ]
    pruningPointHash: str = (
        "5d32a9403273a34b6551b84340a1459ddde2ae6ba59a47987a6374340ba41d5d"
    )
    virtualDaaScore: str = "19989984"


class BlockdagResponse(BaseModel):
    blueScore: int = 260890


class KaspadResponse(BaseModel):
    kaspadHost: str = ""
    serverVersion: str = "0.12.6"
    isUtxoIndexed: bool = True
    isSynced: bool = True
    p2pId: str = "1231312"


class HealthResponse(BaseModel):
    kaspadServers: List[KaspadResponse]


class CoinSupplyResponse(BaseModel):
    circulatingSupply: str = "1000900697580640180"
    maxSupply: str = "2900000000000000000"


class HashrateResponse(BaseModel):
    hashrate: float = 12000132


class KaspadInfoResponse(BaseModel):
    mempoolSize: str = "1"
    serverVersion: str = "0.12.2"
    isUtxoIndexed: bool = True
    isSynced: bool = True
    p2pIdHashed: str = (
        "36a17cd8644eef34fc7fe4719655e06dbdf117008900c46975e66c35acd09b01"
    )
