from sqlalchemy import Column, String, BigInteger, Boolean

from dbsession import Base


class AddressTag(Base):
    __tablename__ = "address_tags"
    address = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    link = Column(String)
