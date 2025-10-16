from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, delete
from database import get_session
from app_final.models.client_models import Client, ClientBase, ClientRead, WorkClass, WorkClassCreate

router = APIRouter()


@router.get("/clients", response_model=list[ClientRead])
def read_clients(session: Session = Depends(get_session)):
    return session.exec(select(Client)).all()


@router.post("/clients", response_model=ClientRead)
def create_client(client: ClientBase, session: Session = Depends(get_session)):
    db_client = Client(**client.dict(exclude={"work_classes"}))
    session.add(db_client)
    session.commit()
    session.refresh(db_client)

    for wc in client.work_classes:
        db_wc = WorkClass(name=wc.name, client_id=db_client.id)
        session.add(db_wc)

    session.commit()
    session.refresh(db_client)
    return db_client


@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, updated_client: ClientBase, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update base fields
    for key, value in updated_client.dict(exclude={"work_classes"}).items():
        setattr(client, key, value)

    # Delete old work classes properly
    old_work_classes = session.exec(
        select(WorkClass).where(WorkClass.client_id == client_id)
    ).all()

    for wc in old_work_classes:
        session.delete(wc)

    # Add new work classes
    for wc in updated_client.work_classes:
        session.add(WorkClass(name=wc.name, client_id=client_id))

    session.commit()
    session.refresh(client)
    return client


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Delete related work_classes first
    session.exec(delete(WorkClass).where(WorkClass.client_id == client_id))

    # Then delete the client
    session.delete(client)
    session.commit()
    return {"detail": "Client deleted"}