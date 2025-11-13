import sys
import json

def example_function(task: dict):
    names = task["files/contents"]
    results_list = []
    for name in names:
        counter = 0
        backwards_name = ""
        for letter in name:
            letter = name[-1 - counter]
            counter+=1
            backwards_name = backwards_name + letter

        result = {
            "name": name,
            "backwards name": backwards_name
        }
        results_list.append(result)
    print(json.dumps(results_list))

task = json.loads(sys.argv[1])
example_function(task)
