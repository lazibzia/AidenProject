from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, delete
from app_final.database import get_session
from app_final.models.client_models import (
    Client, ClientCreate, ClientRead, 
    WorkClass, WorkClassCreate,
    PermitType, PermitTypeCreate,
    PermitClassMapped, PermitClassMappedCreate
)
import json

router = APIRouter()

from sqlalchemy.orm import selectinload

@router.get("/clients", response_model=List[ClientRead])
def read_clients(session: Session = Depends(get_session)):
    statement = (select(Client)
                .options(
                    selectinload(Client.work_classes),
                    selectinload(Client.permit_types),
                    selectinload(Client.permit_classes_mapped)
                ))
    clients = session.exec(statement).all()
    result = []

    for client in clients:
        client_data = client.dict()
        client_data["work_classes"] = [
            {"id": wc.id, "name": wc.name} for wc in client.work_classes
        ]
        client_data["permit_types"] = [
            {"id": pt.id, "name": pt.name} for pt in client.permit_types
        ]
        client_data["permit_classes_mapped"] = [
            {"id": pcm.id, "name": pcm.name} for pcm in client.permit_classes_mapped
        ]
        client_data["keywords_include"] = (
            json.loads(client.keywords_include) if client.keywords_include else None
        )
        client_data["keywords_exclude"] = (
            json.loads(client.keywords_exclude) if client.keywords_exclude else None
        )
        result.append(ClientRead(**client_data))

    return result

@router.post("/clients", response_model=ClientRead)
def create_client(client: ClientCreate, session: Session = Depends(get_session)):
    # Convert lists to JSON strings for database
    db_data = client.dict(exclude={
        "work_classes", 
        "keywords_include", 
        "keywords_exclude",
        "permit_types",
        "permit_classes_mapped"
    })
    db_client = Client(**db_data)

    # Handle keywords
    if client.keywords_include:
        db_client.keywords_include = json.dumps(client.keywords_include)
    if client.keywords_exclude:
        db_client.keywords_exclude = json.dumps(client.keywords_exclude)

    session.add(db_client)
    session.commit()
    session.refresh(db_client)

    # Add work classes
    for wc in client.work_classes:
        db_wc = WorkClass(name=wc.name, client_id=db_client.id)
        session.add(db_wc)

    # Add permit types
    if client.permit_types:
        for pt in client.permit_types:
            db_pt = PermitType(name=pt.name, client_id=db_client.id)
            session.add(db_pt)

    # Add permit classes mapped
    if client.permit_classes_mapped:
        for pcm in client.permit_classes_mapped:
            db_pcm = PermitClassMapped(name=pcm.name, client_id=db_client.id)
            session.add(db_pcm)

    session.commit()
    session.refresh(db_client)

    # Return with lists (original input format)
    response_data = client.dict()
    response_data["id"] = db_client.id
    response_data["work_classes"] = [{"id": wc.id, "name": wc.name} for wc in db_client.work_classes]
    response_data["permit_types"] = [{"id": pt.id, "name": pt.name} for pt in db_client.permit_types]
    response_data["permit_classes_mapped"] = [{"id": pcm.id, "name": pcm.name} for pcm in db_client.permit_classes_mapped]

    return ClientRead(**response_data)

@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, updated_client: ClientCreate, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update base fields (including slider_percentage and priority)
    exclude_fields = {
        "work_classes", 
        "keywords_include", 
        "keywords_exclude",
        "permit_types",
        "permit_classes_mapped"
    }
    for key, value in updated_client.dict(exclude=exclude_fields).items():
        setattr(client, key, value)

    # Handle keywords
    if updated_client.keywords_include:
        client.keywords_include = json.dumps(updated_client.keywords_include)
    else:
        client.keywords_include = None

    if updated_client.keywords_exclude:
        client.keywords_exclude = json.dumps(updated_client.keywords_exclude)
    else:
        client.keywords_exclude = None

    # Delete old work classes
    old_work_classes = session.exec(
        select(WorkClass).where(WorkClass.client_id == client_id)
    ).all()
    for wc in old_work_classes:
        session.delete(wc)

    # Delete old permit types
    old_permit_types = session.exec(
        select(PermitType).where(PermitType.client_id == client_id)
    ).all()
    for pt in old_permit_types:
        session.delete(pt)

    # Delete old permit classes mapped
    old_permit_classes_mapped = session.exec(
        select(PermitClassMapped).where(PermitClassMapped.client_id == client_id)
    ).all()
    for pcm in old_permit_classes_mapped:
        session.delete(pcm)

    # Add new work classes
    for wc in updated_client.work_classes:
        session.add(WorkClass(name=wc.name, client_id=client_id))

    # Add new permit types
    if updated_client.permit_types:
        for pt in updated_client.permit_types:
            session.add(PermitType(name=pt.name, client_id=client_id))

    # Add new permit classes mapped
    if updated_client.permit_classes_mapped:
        for pcm in updated_client.permit_classes_mapped:
            session.add(PermitClassMapped(name=pcm.name, client_id=client_id))

    session.commit()
    session.refresh(client)

    # Return properly formatted response
    client_data = client.dict()
    client_data["work_classes"] = [
        {"id": wc.id, "name": wc.name} for wc in client.work_classes
    ]
    client_data["permit_types"] = [
        {"id": pt.id, "name": pt.name} for pt in client.permit_types
    ]
    client_data["permit_classes_mapped"] = [
        {"id": pcm.id, "name": pcm.name} for pcm in client.permit_classes_mapped
    ]
    client_data["keywords_include"] = (
        json.loads(client.keywords_include) if client.keywords_include else None
    )
    client_data["keywords_exclude"] = (
        json.loads(client.keywords_exclude) if client.keywords_exclude else None
    )

    return ClientRead(**client_data)

@router.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Delete related records first
    session.exec(delete(WorkClass).where(WorkClass.client_id == client_id))
    session.exec(delete(PermitType).where(PermitType.client_id == client_id))
    session.exec(delete(PermitClassMapped).where(PermitClassMapped.client_id == client_id))

    # Then delete the client
    session.delete(client)
    session.commit()
    return {"detail": "Client deleted"}