import sys
import json
import hashlib
from pathlib import Path

def fs_example_function(buf_size, task):
    sha256 = hashlib.sha256()
    results = {}

    work_dir = Path(task["file_path"])
    directory_contents = list(work_dir.iterdir())

    for file in directory_contents:
        with open(str(file),"rb") as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                sha256.update(data)

        results[file.name] = sha256.hexdigest()
    print(json.dumps(results))

task = json.loads(sys.argv[1])
fs_example_function(65536, task)