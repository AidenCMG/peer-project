import requests
import time
import threading
SERVER_URL = "http://127.0.0.1:8000"

heartbeat_time_interval = 180 # seconds
check_for_task_interval = 300 # seconds

client_state = {
    "id": "",
    "currentStatus": "idle",
    "current_tasks": []
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
        print(response.text)
        print(task_data["payload"]["image"]["file"])
        client_state["current_tasks"].append(task_data)
        return True

    return False




def send_heartbeat(): #Currently heartbeat is the only way the client status is updated.
    data = {
    "node_id": client_state["id"],
    "status": client_state["currentStatus"]
    }
    response = requests.post(f"{SERVER_URL}/heartbeat", json=data)
    print(response.text)
    
def submit_result():
    data = {
        "task_id": client_state["current_tasks"][0]["id"],
        "result": {
            "output": "placeholder output"
        }
    }
    response = requests.post(f"{SERVER_URL}/submit-result", json=data)


def heartbeat_worker():
    while True:
        send_heartbeat()
        time.sleep(heartbeat_time_interval)


def main():
    register_client() #Make this one time only
    #Best way to do this?
    #config file?

    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    keepGoing = True
    while keepGoing:
        if client_state["currentStatus"] == "idle":
            got_task = get_new_task()

            if got_task:
                client_state["currentStatus"] = "busy"
                send_heartbeat()
                #solve task
                submit_result()
                client_state["currentStatus"] = "idle"
                send_heartbeat()
            else:
                time.sleep(check_for_task_interval)




