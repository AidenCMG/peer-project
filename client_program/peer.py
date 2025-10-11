import requests
import time
import threading
from pathlib import Path
import subprocess
import os
import json

SERVER_URL = "http://127.0.0.1:8000"

heartbeat_time_interval = 180 # seconds
check_for_task_interval = 300 # seconds

client_state = {
    "id": "",
    "currentStatus": "idle",
    "current_tasks": [],
    "installed_modules": set(),
    "last_result": {}
}

supported_languages = {
    ".py": "python",
    ".js": "nodejs",

    #java
}

def register_client():
    data = {
    "hardware": {
        "cpu": "placeholder cpu",
        "memory": "4gb",
        "gpu": "placeholder gpu"
    },
    "installed_modules": ["placeholder_module"]
    }
    response = requests.post(f"{SERVER_URL}/register", json=data)
    client_data = response.json()
    client_state["id"] = client_data["node_id"]
    
    
def get_new_task():
    response = requests.post(f"{SERVER_URL}/get-task",params={"node_id": client_state["id"]})
    task_data = response.json()
    if "detail" not in task_data:
        #print(response.text)
        #print(task_data["payload"]["image"]["file"])
        client_state["current_tasks"].append(task_data)
        return True

    return False




def send_heartbeat():
    data = {
    "node_id": client_state["id"],
    "status": client_state["currentStatus"]
    }
    response = requests.post(f"{SERVER_URL}/heartbeat", json=data)
    #print(response.text)
    
def submit_result():
    data = {
        "task_id": client_state["current_tasks"][0]["id"],
        "result": client_state["last_result"]
    }
    response = requests.post(f"{SERVER_URL}/submit-result", json=data)


def heartbeat_worker():
    while True:
        send_heartbeat()
        time.sleep(heartbeat_time_interval)

def get_installed_modules():
    path = Path("client_program/modules")
    directory_contents = list(path.iterdir())
    for item in directory_contents:
        client_state["installed_modules"].add(item.name)
    #print(client_state["installed_modules"])



def run_module_subprocess():
    serialized_task = json.dumps(client_state["current_tasks"][0]["payload"])
    module = client_state["current_tasks"][0]["module"]
    module_path = Path(f"client_program/modules/{module}")
    interpreter = supported_languages.get(module_path.suffix)
    try:
        if interpreter:
            command = [interpreter, str(module_path), serialized_task]
        elif module_path.suffix == ".class":
            command = ["java", "-cp", str(module_path.parent), module_path.stem, serialized_task]
        elif os.access(str(module_path), os.X_OK):
            command = [str(module_path)]

        response = subprocess.run(command,capture_output=True,text=True,check=True)
    except subprocess.CalledProcessError as e:
        print(f"Stderr from child:\n{e.stderr}")

    
    #print(json.loads(response.stdout))
    client_state["last_result"]["result"] = json.loads(response.stdout)


def main():
    register_client() #Make this one time only
    #Best way to do this?
    #config file?
    get_installed_modules()

    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    keepGoing = True
    while keepGoing:
        if client_state["currentStatus"] == "idle":
            print("Checking for new task...")
            got_task = get_new_task()

            if got_task:
                print("Got task")
                client_state["currentStatus"] = "busy"
                send_heartbeat()
                run_module_subprocess()
                print("Task complete!\nSending results to server...")

                submit_result()
                client_state["currentStatus"] = "idle"
                send_heartbeat()
                print("Results submitted!")
            else:
                print(f"No task available. Waiting {check_for_task_interval} seconds")
                time.sleep(check_for_task_interval)




#get_installed_modules()
#client_state["current_tasks"].append({"name": "Aiden", "module": "example_module.py"})
#run_module_subprocess()
main()