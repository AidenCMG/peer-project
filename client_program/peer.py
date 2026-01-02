import requests
import time
import threading
from pathlib import Path
import subprocess
import os
import json
import platform
import zipfile
import shutil

class Peer:

    def __init__(self, server_url="http://127.0.0.1:8000", heartbeat_interval=180, task_check_interval=300):
        self.server_url = server_url
        self.heartbeat_time_interval = heartbeat_interval
        self.check_for_task_interval = task_check_interval

        self.id = None,
        self.status = "idle"
        self.current_task = None
        self.last_result = {}
        self.work_dir = Path("temp_files")
        self.installed_modules = set() 
        self._load_installed_modules()

        self.supported_languages = {
            ".py": "python",
            ".js": "nodejs",
            #java
        }

    def _safe_post(self, endpoint, **kwargs):
        #Helper for making HTTP POST requests safely.
        try:
            url = f"{self.server_url}/{endpoint}"
            response = requests.post(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request Error ({endpoint}): {e}")
            return None
        
    def _load_installed_modules(self):
        #Scans the modules directory.
        path = Path("client_program/modules")
        if path.exists():
            for item in path.iterdir():
                self.installed_modules.add(item.name)


    def register(self):
        #Registers the client with the server.
        data = {
            "hardware": {
                "cpu": platform.processor(),
                "memory": "4gb", 
                "gpu": "placeholder gpu"
            },
            "installed_modules": list(self.installed_modules)
        }
        response = self._safe_post("register", json=data)
        if response:
            client_properties = response.json()
            self.id = client_properties.get("node_id")
            print(f"Registered with ID: {self.id}")
            return True
        return False
    
    def get_new_task(self):
        response = self._safe_post("get-task",params={"node_id": self.id})
        if response:
            task_data = response.json()
            if "payload" in task_data:
                self.current_task = task_data
                return True
        return False
    
    def download_task_file(self):
        token = self.current_task.get("download_token")
        if not token:
            return None
        self.work_dir.mkdir()
        try:
            url = f"{self.server_url}/download/{token}"
            response = requests.get(url, stream=True)
            response.raise_for_status()
            filename = "download.zip"
            if "content-disposition" in response.headers:
                filename = response.headers["content-disposition"].split("filename=")[1].strip("'")

            filepath = self.work_dir/filename
            with open(filepath,'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(filepath,"r") as zf:
                zf.extractall()

        except Exception as e:
            print(f"File download failed: {e}")
            return None


    def send_heartbeat(self):
        #Send status update to server
        if not self.id:
            return None
        data = {
            "node_id": self.id,
            "status": self.status
        }
        response = self._safe_post("heartbeat", json=data)

    def _heartbeat_worker(self):
        while True:
            try:
                self.send_heartbeat()
            except Exception as e:
                print(f"Unexpected error while sending heartbeat: {e}")
            time.sleep(self.heartbeat_time_interval)
        
    def run_module_subprocess(self, file_path):
        task = self.current_task["payload"]
        if file_path:
            task["file_path"] = str(file_path)
        serialized_task = json.dumps(task)
        
        module = self.current_task["module"]
        module_path = Path(f"client_program/modules/{module}")

        interpreter = self.supported_languages.get(module_path.suffix)
        try:
            if interpreter:
                command = [interpreter, str(module_path), serialized_task]
            elif module_path.suffix == ".class":
                command = ["java", "-cp", str(module_path.parent), module_path.stem, serialized_task]
            elif os.access(str(module_path), os.X_OK):
                command = [str(module_path)]
            else:
                raise ValueError("Unsupported module language")
            
            response = subprocess.run(command,capture_output=True,text=True,check=True)
            #print(json.loads(response.stdout))
            self.last_result = json.loads(response.stdout)

        except subprocess.CalledProcessError as e:
            print(f"Stderr from child:\n{e.stderr}")
        except json.JSONDecodeError:
            print("Error: invalid JSON output from module")
        except Exception as e:
            print(f"Unexpected error while running subprocess: {e}")

    def submit_result(self):
        data = {
            "task_id": self.current_task["id"],
            "result": self.last_result
        }
        self._safe_post("submit-result", json=data)
        self.current_task = None
        self.last_result = {}

    def cleanup_files(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

    def run(self):
        if not self.register():
            print("Failed to Register. Goodbye...")
            return
        
        hb_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        hb_thread.start()

        while True:
            if self.status == "idle":
                print("Checking for task...")
                if self.get_new_task():
                    print("Task received.")
                    self.status = "busy"
                    self.send_heartbeat()

                    try:
                        file_path = self.download_task_file()
                        self.run_module_subprocess(file_path)
                        print("Task complete. Submitting...")
                        self.submit_result()
                    finally:
                        self.cleanup_files()
                        self.status = "idle"
                        self.send_heartbeat()
                else:
                    print(f"No task available. Waiting {self.check_for_task_interval} seconds")
                    time.sleep(self.check_for_task_interval)

if __name__ == "__main__":
    client = Peer()
    client.run()