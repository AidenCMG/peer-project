from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Client, Task
from schemas import ClientRegister, Heartbeat, TaskResult, TaskSchema
import uuid

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register_client(client: ClientRegister, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.node_id == client.node_id).first()
    if not db_client:
        db_client = Client(
            node_id=client.node_id,
            hardware=client.hardware,
            installed_modules=client.installed_modules,
            status="idle"
        )
        db.add(db_client)
    else:
        db_client.hardware = client.hardware
        db_client.installed_modules = client.installed_modules
        db_client.status = "idle"
    db.commit()
    return {"message": "Registered"}

@app.post("/heartbeat")
def heartbeat(hb: Heartbeat, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.node_id == hb.node_id).first()
    if not client:
        raise HTTPException(404, "Client not found")
    client.status = hb.status
    db.commit()
    return {"message": "Heartbeat received"}

@app.post("/get-task")
def get_task(node_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.assigned_to == None).first()
    if not task:
        raise HTTPException(404, "No task available")
    task.assigned_to = node_id
    task.status = "running"
    db.commit()
    return TaskSchema.from_orm(task)

@app.post("/submit-result")
def submit_result(result: TaskResult, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == result.task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "completed"
    task.result = result.result
    db.commit()
    return {"message": "Result submitted"}

@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()
