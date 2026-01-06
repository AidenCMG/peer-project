from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

#SQLAlchemy Models

class Client(Base):
    __tablename__ = "clients"
    node_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    installed_modules = Column(JSON)
    hardware = Column(JSON)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    module = Column(String)
    payload = Column(JSON)
    download_token = Column(String, nullable=True)
    status = Column(String, default ="pending")
    assigned_to = Column(String, ForeignKey("clients.node_id"), nullable=True)
    verified_by = Column(String, ForeignKey("clients.node_id"), nullable=True)
    result1 = Column(JSON, nullable=True)
    result2 = Column(JSON, nullable=True)
    files = relationship("File", back_populates="owner_task")

class File(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"))
    path = Column(String)
    owner_task = relationship("Task", back_populates="files")