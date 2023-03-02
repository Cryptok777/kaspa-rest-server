from sqlalchemy import Column, String, BigInteger, Boolean

from dbsession import Base


class AddressBalance(Base):
    __tablename__ = "address_balances"
    address = Column(String, primary_key=True)
    balance = Column(BigInteger)
