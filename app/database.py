"""Engine MySQL e sessões transacionais SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.base import Base
from app.config import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
