from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Client, Task, File
from .schemas import ClientRegister, Heartbeat, ClientSchema, TaskResult, TaskSchema, TaskCreate
import uuid
import zipfile
import io
import os
import time
import threading

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


#Rewrite this to be less confusing
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
    task.assignment_time = time.time()
    task.status = "running"
    db.commit()
    return task

@app.post("/admin/create-task", response_model=TaskSchema)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db), _: None = Depends(localhost_only)):
    file_objects = []
    if task_data.file_paths:
        
        for file_path in task_data.file_paths:
            file_objects.append(File(path=file_path))

    new_task = Task(
            module=task_data.module,
            payload=task_data.payload,
            status="pending",
            files=file_objects
        )    
    if file_objects:
       new_task.download_token=str(uuid.uuid4())

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task



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

@app.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.download_token==token).first()
    if not task:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w") as zip_file:
        for file_obj in task.files:
            archive_name = os.path.basename(file_obj.path)
            zip_file.write(file_obj.path,arcname=archive_name)
    zip_buffer.seek(0)

    headers = {"Content-Disposition": f"attachement; filename='download_{token}.zip'"}

    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed",headers=headers)

#somehow add queue

# if task status running 24 hours after assignment reset status to pending
def reset_tasks(db: Session):
    timeout_value = time.time() - (24*3600)   #Hours to seconds
    stale_tasks = db.query(Task).filter(Task.status == "running", Task.assignment_time < timeout_value)
    stale_tasks.update(
        {Task.status: "pending",
        Task.assigned_to: None,
        Task.verified_by: None,
        Task.assignment_time: None}, synchronize_session=False)
    db.commit()
    
def reset_task_loop():
    while True:
        db = SessionLocal()
        try:
            reset_tasks(db)
        except Exception as e:
            print(f"Error running background thread: {e}")
        finally:
            db.close()
        time.sleep(24*3600)

reset_thread = threading.Thread(target=reset_task_loop, daemon=True)
reset_thread.start()
