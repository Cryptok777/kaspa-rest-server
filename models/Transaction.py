from sqlalchemy import Column, String, Integer, BigInteger, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY

from dbsession import Base


class Transaction(Base):
    __tablename__ = "transactions"
    subnetwork_id = Column(String)  # "0000000000000000000000000000000000000000",
    transaction_id = Column(
        String, primary_key=True
    )  # "bedea078f74f241e7d755a98c9e39fda1dc56491dc7718485a8f221f73f03061",
    hash = Column(
        String
    )  # "a5f99f4dc55693124e7c6b75dc3e56b60db381a74716046dbdcae9210ce1052f",
    mass = Column(String)  # "2036",
    block_hash = Column(
        ARRAY(String)
    )  # "1b41af8cfe1851243bedf596b7299c039b86b2fef8eb4204b04f954da5d2ab0f",
    block_time = Column(BigInteger)  # "1663286480803"
    is_accepted = Column(Boolean, default=False)
    accepting_block_hash = Column(String, nullable=True)


class TransactionOutput(Base):
    __tablename__ = "transactions_outputs"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    index = Column(Integer)
    amount = Column(BigInteger)
    script_public_key = Column(String)
    script_public_key_address = Column(String)
    script_public_key_type = Column(String)
    accepting_block_hash = Column(String)


class TransactionInput(Base):
    __tablename__ = "transactions_inputs"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String)
    index = Column(Integer)

    previous_outpoint_hash = Column(
        String
    )  # "ebf6da83db96d312a107a2ced19a01823894c9d7072ed0d696a9a152fd81485e"
    previous_outpoint_index = Column(
        Integer
    )  # "ebf6da83db96d312a107a2ced19a01823894c9d7072ed0d696a9a152fd81485e"

    signature_script = Column(String)  # "41c903159094....281a1d26f70b0037d600554e01",
    sig_op_count = Column(Integer)
