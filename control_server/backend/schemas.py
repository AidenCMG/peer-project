from pydantic import BaseModel
from typing import Optional, List, Dict

class ClientRegister(BaseModel):
    node_id: str
    hardware: Dict
    installed_modules: List[str]

class Heartbeat(BaseModel):
    node_id: str
    status: str

class TaskSchema(BaseModel):
    id: str
    module: str
    payload: dict
    status: str
    assigned_to: Optional[str] = None

class TaskResult(BaseModel):
    task_id: str
    result: dict
