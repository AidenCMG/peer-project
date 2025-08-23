from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Client, Task
from .schemas import ClientRegister, Heartbeat, ClientSchema, TaskResult, TaskSchema, TaskCreate
import uuid

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=ClientSchema)
def register_client(client: ClientRegister, db: Session = Depends(get_db)):
    db_client = Client(
        node_id=str(uuid.uuid4()),
        hardware=client.hardware,
        installed_modules=client.installed_modules,
        status="idle"
        )
    db.add(db_client)
    db.commit()
    return db_client

@app.post("/heartbeat", response_model=ClientSchema)
def heartbeat(hb: Heartbeat, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.node_id == hb.node_id).first()
    if not client:
        raise HTTPException(404, "Client not found")
    client.status = hb.status
    client.installed_modules = hb.installed_modules
    db.commit()
    return client

@app.post("/get-task", response_model=TaskSchema)
def get_task(node_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.assigned_to == None).first()
    if not task:
        raise HTTPException(404, "No task available")
    task.assigned_to = node_id
    task.status = "running"
    db.commit()
    return task

@app.post("/create-task", response_model=TaskSchema)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        module=task_data.module,
        payload=task_data.payload,
        status="pending"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task
    
@app.post("/submit-result", response_model=TaskSchema)
def submit_result(result: TaskResult, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == result.task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "completed"
    task.result = result.result
    db.commit()
    return task

@app.get("/clients", response_model=list[ClientSchema])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()

@app.get("/tasks", response_model=list[TaskSchema])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()
