from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    pool = Column(String, nullable=False)
    chain = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    token = Column(String, nullable=False)
    tx_hash = Column(String, nullable=True)
    gas_cost = Column(Float, default=0)
    simulated_pnl = Column(Float, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentState(Base):
    __tablename__ = "agent_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String, nullable=False, default="stopped")
    last_run = Column(DateTime(timezone=True), nullable=True)
    config = Column(JSON, nullable=True)


def init_db(database_url: str = "sqlite:///agent-heap.db"):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
