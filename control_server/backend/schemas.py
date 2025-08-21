from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict

class ClientRegister(BaseModel):
    node_id: str
    hardware: Dict
    installed_modules: List[str]
    model_config = ConfigDict(from_attributes=True)

class Heartbeat(BaseModel):
    node_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class ClientSchema(BaseModel):
    node_id: str
    status: str
    hardware: Dict
    installed_modules: List[str]
    last_seen: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TaskSchema(BaseModel):
    id: str
    module: str
    payload: dict
    status: str
    assigned_to: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TaskResult(BaseModel):
    task_id: str
    result: dict
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    module: str
    payload: dict
    model_config = ConfigDict(from_attributes=True)