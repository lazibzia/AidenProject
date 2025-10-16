from sqlmodel import create_engine, Session
import os


  # Add this

sqlite_file_name = "permits.db"
print("📁 DB absolute path:", os.path.abspath(sqlite_file_name))
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def get_session():
    with Session(engine) as session:
        yield session
