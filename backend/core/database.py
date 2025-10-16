from sqlmodel import SQLModel, Session, create_engine
import sqlite3
from typing import Generator
from app.config.settings import settings

# SQLModel engine for clients
engine = create_engine(f"sqlite:///{settings.CLIENTS_DB_PATH}")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def get_permits_db_connection():
    """Get connection to permits database"""
    return sqlite3.connect(settings.PERMITS_DB_PATH)

def get_clients_db_connection():
    """Get connection to clients database"""
    return sqlite3.connect(settings.CLIENTS_DB_PATH)