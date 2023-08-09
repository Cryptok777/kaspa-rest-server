from sqlalchemy import Column, String, BigInteger, TIMESTAMP

from dbsession import Base


class AddressBalancesRecord(Base):
    __tablename__ = "address_balances_records"
    address = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False), primary_key=True)
    balance = Column(BigInteger)
