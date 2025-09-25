from fastapi import FastAPI, Depends, HTTPException, Request
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

def localhost_only(request: Request): #Make sure to configure proxy correctly or this won't work
    if request.client.host not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Forbidden")
 
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
    #client.installed_modules = hb.installed_modules
    db.commit()
    return client


#Goals for this rewrite
#1. Each task needs to be verified by two seperate clients
#2. This means we need to keep track of which clients have done the task
#3. Remove task from pool once completed and verified.
#4. If verification fails keep in pool until a consensus is reached

@app.post("/get-task", response_model=TaskSchema) #Right now this doesn't care if it is verified by the same node
def get_task(node_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.assigned_to == None).first()
    if not task:
        unverified_task = db.query(Task).filter(Task.verified_by == None,Task.result1 != None).first()
        if not unverified_task:
            raise HTTPException(404, "No task available")
        unverified_task.verified_by = node_id
        unverified_task.status = "verifying"
        db.commit()
        return unverified_task
    task.assigned_to = node_id
    task.status = "running"
    db.commit()
    return task

@app.post("/admin/create-task", response_model=TaskSchema)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db), _: None = Depends(localhost_only)):
    new_task = Task(
        module=task_data.module,
        payload=task_data.payload,
        status="pending"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


#As part of this rework we need to have submit result distingush between a first and second submit
@app.post("/submit-result", response_model=TaskSchema)
def submit_result(result: TaskResult, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == result.task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    
    if task.result1 == None:
        task.result1 = result.result
        task.status = "unverified"
        db.commit()
        
    else:
        task.result2 = result.result
        if task.result1 == task.result2:
            task.status = "completed"
        else:
            task.verified_by = None
            task.assigned_to = None
            task.result1 = None
        db.commit()
    return task

@app.get("/admin/clients", response_model=list[ClientSchema])
def get_clients(db: Session = Depends(get_db), _: None = Depends(localhost_only)):
    return db.query(Client).all()

@app.get("/admin/tasks", response_model=list[TaskSchema])
def get_tasks(db: Session = Depends(get_db), _: None = Depends(localhost_only)):
    return db.query(Task).all()

 

#somehow add queue