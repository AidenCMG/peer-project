import sys
import json

def example_function(task: dict):
    counter = 0
    backwards_name = ""
    for letter in task["name"]:
        letter = task["name"][-1 - counter]
        counter+=1
        backwards_name = backwards_name + letter
    
    result = {
        "name": task["name"],
        "backwards name": backwards_name
    }
    print(json.dumps(result))

task = json.loads(sys.argv[1])
example_function(task)
