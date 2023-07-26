from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    summary: Optional[str] = ""
    classification: Optional[str] = "INTERNAL"
    authorization_scope: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DeviceTarget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    name: str
    kind: Optional[str] = "generic"
    vendor: Optional[str] = ""
    model: Optional[str] = ""
    firmware_version: Optional[str] = ""
    environment: Optional[str] = "lab"
    notes: Optional[str] = ""
    tags: List[str] = []

class HardwareSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    target_id: Optional[str] = None
    interface_type: Optional[str] = "USB"
    connection_method: Optional[str] = "direct"
    adapter: Optional[str] = ""
    configuration: Optional[str] = ""
    observations: Optional[str] = ""
    artifacts: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvidenceArtifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    target_id: Optional[str] = None
    session_id: Optional[str] = None
    kind: Optional[str] = "photo"
    path: str
    sha256: Optional[str] = ""
    notes: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    state: str = "DRAFT"
    summary: Optional[str] = ""
    findings: List[dict] = []
    generated_at: Optional[datetime] = None

class AgentTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    mode: str = "summarize"
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    state: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)
