from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Client, ClientCreate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/clients", response_model=list[Client])
def read_clients(session: Session = Depends(get_session)):
    return session.exec(select(Client)).all()

@app.post("/clients", response_model=Client)
def create_client(client: ClientCreate, session: Session = Depends(get_session)):
    db_client = Client(**client.dict())
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.put("/clients/{client_id}", response_model=Client)
def update_client(client_id: int, updated_client: ClientCreate, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in updated_client.dict().items():
        setattr(client, key, value)
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    session.delete(client)
    session.commit()
    return {"success": True}
