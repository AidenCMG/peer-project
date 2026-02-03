# So you want to make a module eh?  
This guide covers the basics of ensuring your module is compatible with the project. 
   

## Task formatting  

When making a module it is important to create an outline of the structure of a task.  
A task is composed of a payload that contains multiple fields. These fields are specific to what is required by the module and should be listed out when submitting a module. 
   
The cli has a list of approved modules that contains important information for the format of the task.  
```
modules = {
    "example_module.py": {"fields":[], "payload_field":"names","needs_file":True,"needs_folder":False},
    "fs_example_module.py": {"fields":[],"needs_file":False,"needs_folder":True},
}
```


#### The server can take three types of input to create a task.
1. A text file -For any module that requires a large amount of unique text input like wordlists.  
2. A folder -Contains any other filetype (images, sound clips, etc.)
3. Manual text input -For modules that utilize a command style of input.

Note that the cli will parse a text file line by line.


## Working with a task   
The task data will be passed to your module as json. You will need to handle parsing it into your languages native data structure (Python: dict, Java: hashmap, etc)  

The result must be sent to stdout as a json string. Because of this, keep stdout clear of any other messages.   

Refer to the example modules for implementation help.  