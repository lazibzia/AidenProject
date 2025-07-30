from typing import Optional
from sqlmodel import SQLModel, Field

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
    permit_type: Optional[str] = None
    status: str = "active"

class Client(ClientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ClientCreate(ClientBase):
    pass
