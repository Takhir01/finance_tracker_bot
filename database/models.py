from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    is_allowed = Column(Boolean, default=True)
    invited_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    type = Column(String(20), nullable=False, default="expense")  # 'expense' or 'income'
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="сум")
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    receipt_path = Column(String(500), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="transactions")


class AccessLink(Base):
    __tablename__ = "access_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    created_by = Column(BigInteger, nullable=False)
    is_active = Column(Boolean, default=True)
    uses_count = Column(Integer, default=0)
    max_uses = Column(Integer, default=-1)  # -1 means unlimited
    created_at = Column(DateTime, default=datetime.utcnow)
