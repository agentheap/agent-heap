import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schema import Base, AgentState, Trade


def get_engine():
    url = os.getenv("DATABASE_URL", "sqlite:///agent-heap.db")
    return create_engine(url)


def get_session():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def save_trade(
    action: str, amount: float, token: str, simulated_pnl: float = 0
) -> Trade:
    session = get_session()
    trade = Trade(
        action=action, amount=amount, token=token, simulated_pnl=simulated_pnl
    )
    session.add(trade)
    session.commit()
    session.close()
    return trade


def get_agent_state() -> AgentState | None:
    session = get_session()
    state = session.query(AgentState).order_by(AgentState.id.desc()).first()
    session.close()
    return state


def set_agent_status(status: str) -> None:
    session = get_session()
    state = get_agent_state()
    if state:
        state.status = status
    else:
        state = AgentState(status=status, config={})
        session.add(state)
    session.commit()
    session.close()


def get_recent_trades(limit: int = 10) -> list[Trade]:
    session = get_session()
    trades = session.query(Trade).order_by(Trade.id.desc()).limit(limit).all()
    session.close()
    return trades
