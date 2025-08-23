from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
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
    status = Column(String, default ="pending")
    assigned_to = Column(String, ForeignKey("clients.node_id"), nullable=True)
    result = Column(JSON, nullable=True)
