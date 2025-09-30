from pydantic import BaseModel, ConfigDict
from typing import Optional 
from datetime import datetime

# Pydantic Schemas

class ClientRegister(BaseModel):
    #node_id: str
    hardware: dict[str,str]
    installed_modules: list[str]
    model_config = ConfigDict(from_attributes=True)

class Heartbeat(BaseModel):
    node_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class ClientSchema(BaseModel):
    node_id: str
    status: str
    hardware: dict[str,str]
    installed_modules: list[str]
    last_seen: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TaskSchema(BaseModel):
    id: str
    module: str
    payload: dict
    status: str
    assigned_to: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    result1: Optional[dict] = None
    result2: Optional[dict] = None

class TaskResult(BaseModel):
    task_id: str
    result: dict
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    module: str
    payload: dict
    model_config = ConfigDict(from_attributes=True)