from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import json

class WorkClass(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    client_id: int = Field(foreign_key="client.id")
    client: Optional["Client"] = Relationship(back_populates="work_classes")

# new table: permit types (one client -> many permit types)
class PermitType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    client_id: int = Field(foreign_key="client.id")
    client: Optional["Client"] = Relationship(back_populates="permit_types")

# new table: permit classes mapped (one client -> many mapped classes)
class PermitClassMapped(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    client_id: int = Field(foreign_key="client.id")
    client: Optional["Client"] = Relationship(back_populates="permit_classes_mapped")

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
    status: str = "active"
    slider_percentage: int = Field(default=100, ge=1, le=100)  # 1-100%
    priority: int = Field(default=999, ge=1)  # Lower number = higher priority

class Client(ClientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    work_classes: List[WorkClass] = Relationship(back_populates="client")

    # relationships for permit types and mapped classes
    permit_types: List[PermitType] = Relationship(back_populates="client")
    permit_classes_mapped: List[PermitClassMapped] = Relationship(back_populates="client")

    keywords_include: Optional[str] = None  # JSON string in DB
    keywords_exclude: Optional[str] = None  # JSON string in DB

    # convenience helpers for keywords (unchanged behavior)
    @property
    def keywords_include_list(self) -> List[str]:
        if self.keywords_include:
            try:
                return json.loads(self.keywords_include)
            except Exception:
                return []
        return []

    @keywords_include_list.setter
    def keywords_include_list(self, values: Optional[List[str]]):
        try:
            self.keywords_include = json.dumps(values or [])
        except Exception:
            self.keywords_include = None

    @property
    def keywords_exclude_list(self) -> List[str]:
        if self.keywords_exclude:
            try:
                return json.loads(self.keywords_exclude)
            except Exception:
                return []
        return []

    @keywords_exclude_list.setter
    def keywords_exclude_list(self, values: Optional[List[str]]):
        try:
            self.keywords_exclude = json.dumps(values or [])
        except Exception:
            self.keywords_exclude = None

# Read/create models for WorkClass (unchanged)
class WorkClassRead(SQLModel):
    id: int
    name: str

class WorkClassCreate(SQLModel):
    name: str

# Read/create models for PermitType
class PermitTypeRead(SQLModel):
    id: int
    name: str

class PermitTypeCreate(SQLModel):
    name: str

# Read/create models for PermitClassMapped
class PermitClassMappedRead(SQLModel):
    id: int
    name: str

class PermitClassMappedCreate(SQLModel):
    name: str

class ClientCreate(ClientBase):
    work_classes: List[WorkClassCreate] = []
    keywords_include: Optional[List[str]] = None  # List in API
    keywords_exclude: Optional[List[str]] = None  # List in API
    # accept lists of permit types / mapped classes in API
    permit_types: Optional[List[PermitTypeCreate]] = None
    permit_classes_mapped: Optional[List[PermitClassMappedCreate]] = None

class ClientRead(ClientBase):
    id: int
    work_classes: List[WorkClassRead]
    keywords_include: Optional[List[str]] = None  # List in API
    keywords_exclude: Optional[List[str]] = None  # List in API
    # return lists for permit types / mapped classes
    permit_types: Optional[List[PermitTypeRead]] = None
    permit_classes_mapped: Optional[List[PermitClassMappedRead]] = None