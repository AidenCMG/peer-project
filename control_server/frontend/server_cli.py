
import requests
import shlex
import argparse
import json
import time
import sys


SERVER_URL = "http://127.0.0.1:8000"


def create_task(command_args: list):
    parser = argparse.ArgumentParser(prog="create_task", description="Creates a new task on the server")
    parser.add_argument("--module", required=True, help="The name of the module for the task.")
    parser.add_argument("--payload", required=True, help="A JSON string representing the task's payload.")

    args=parser.parse_args(command_args)

    data = {
        "module": args.module,
        "payload": json.loads(args.payload)
    }
    requests.post(f"{SERVER_URL}/admin/create-task", json=data)


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
    "dance_party": dance_party
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