from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class WorkClass(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    client_id: int = Field(foreign_key="client.id")

    # Back reference
    client: Optional["Client"] = Relationship(back_populates="work_classes")


class ClientBase(SQLModel):
    name: str
    company: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    rag_query: str
    rag_filter_json: str
    permit_type: Optional[str] = None
    permit_class_mapped: Optional[str] = None
    work_classes: List[WorkClass] = []
    status: str = "active"


class Client(ClientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # One-to-many relationship
    work_classes: List[WorkClass] = Relationship(back_populates="client")


class WorkClassRead(SQLModel):
    id: int
    name: str


class ClientRead(ClientBase):
    id: int
    work_classes: List[WorkClassRead]


class WorkClassCreate(SQLModel):
    name: str


class ClientCreate(ClientBase):
    work_classes: List[WorkClassCreate] = []