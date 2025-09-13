
import requests
import shlex
import argparse
import time
import sys
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"


def create_task(command_args: list):
    parser = argparse.ArgumentParser(prog="create_task", description="Creates a new task on the server")
    parser.add_argument("-m", "--module", required=True, help="The name of the module for the task.")

    args=parser.parse_args(command_args)
    payload = get_payload()
    
    data_to_post = {
        "module": args.module,
        "payload": payload
    }
    requests.post(f"{SERVER_URL}/admin/create-task", json=data_to_post)

def batch_create(command_args: list):
    parser = argparse.ArgumentParser(prog="batch_create", description="Creates tasks in batches")
    parser.add_argument("-m", "--module", required=True, help="The name of the module for the tasks.")
    parser.add_argument("-c", "--chunks", required=True, help="Size of chunks to use")
    parser.add_argument("-l", "--label", required=True,  help="Label specifiying what the file is")

    args=parser.parse_args(command_args)
 
    payload_data = get_module_fields()
    chunker = make_chunker(int(args.chunks),args.label) #make this upload specified filepath instead of returning list
    
    for chunk in chunker:
        payload_data[args.label] = chunk

        data_to_post = {
            "module": args.module,
            "payload": payload_data
        }
        requests.post(f"{SERVER_URL}/admin/create-task", json=data_to_post) #Swap this for file download url
    

def get_payload():
    label = input("Enter label: ")
    path = input("Enter path to file: ")

    common_data = get_module_fields()
    common_data[label] = path
    return (common_data)


def get_module_fields():
    keepGoing = True
    data_holder = {}
    while(keepGoing):
        field_name = input("Enter the name of the field: ")
        field_value = input("Enter the fields value: ")
        data_holder[field_name] = field_value

        response = input("Enter another field?\n1) Yes\n2) No\n")
        if response == "2":
            keepGoing = False
            return data_holder
        
def make_chunker(chunk_size: int, label: str):
    path = Path(input("Enter path to file/files: "))
    if path.is_dir():
        directory_contents = list(path.iterdir())

        for i in range(0, len(directory_contents),chunk_size):
            chunk = directory_contents[i:i+chunk_size]

            str_paths = []
            for p in chunk:
                str_paths.append(str(p))
            yield str_paths
            
    elif path.is_file():      #For text files
        directory_name = Path("split_files")
        directory_name.mkdir()
            
        file_contents = path.read_text()
        lines = file_contents.splitlines()
        for i in range(0,len(lines), chunk_size):
            chunk = lines[i:i+chunk_size]
            file_path = directory_name/str(i)
            file_path.write_text("\n".join(chunk))
            
            yield str(file_path)
        
    else:
        print("specified path does not exist")
            
 

    
def list_tasks(_):
    response = requests.get(f"{SERVER_URL}/admin/tasks")
    all_tasks = response.json()
    for task in all_tasks:
        print(f"ID: {task["id"]}\nModule: {task["module"]}\nPayload: {task["payload"]}\nStatus: {task["status"]}\nAssigned to: {task["assigned_to"]}\n")


def list_clients(_):
    response = requests.get(f"{SERVER_URL}/admin/clients")
    all_clients = response.json()
    for client in all_clients:
        print(f"ID: {client["node_id"]}\nStatus: {client["status"]}\n")


def dance_party(_):
    print("Party Time!")
    dance_moves = [
        "(>'-')>",
        "<('-'<)",
        "( ^'-')^",
        "v('-'v)",
        "(>'-')>",
        "<('-'<)",
        " (^'-')^ "
    ]
    try:
        while True:
            for move in dance_moves:
                sys.stdout.write(f'\r{move}')
                sys.stdout.flush()
                time.sleep(0.2) 
    except KeyboardInterrupt:   
        print("\nParty Over!")


command_mapper = {
    "create_task": create_task,
    "list_tasks": list_tasks,
    "list_clients": list_clients,
    "dance_party": dance_party,
    "batch_create": batch_create
}

def run():
    print("Starting server cli. Use 'quit' or 'q' to leave.")

    keepGoing = True
    while keepGoing:
        line = input(">> ")
        if line.lower() == "quit" or line.lower() == "q":
            keepGoing = False
        else:
            args = shlex.split(line)
            print(args)
            command = args[0]
            command_args = args[1:]
            command_mapper[command](command_args)

run()