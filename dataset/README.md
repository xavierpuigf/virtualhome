
## Environment
VirtualHome is composed of 7 scenes where activities can be executed. Each scene is encoded in a .json file containing a node for every object and edges between them representing relationships. They can be modified through the corresponding json file. 

The files representing each apartment can be found in `example_graphs`.

Check `example_scripts/` for examples on how to read and update graphs.

| Scene 1   | Scene 2   | Scene 3   | Scene 4   | Scene 5   | Scene 6   | Scene 7  |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |------------- |
| ![img](../assets/scene1rot.png) | ![img](..//assets/scene2rot.png)| ![img](..//assets/scene3rot.png)| ![img](..//assets/scene4rot.png)| ![img](..//assets/scene5rot.png)| ![img](..//assets/scene6rot.png)| ![img](..//assets/scene7rot.png)


## Programs
Activities in VirtualHome are executed through programs. Each program is a sequence of instructions representing atomic actions that the agent will execute. Each program is stored in a .txt file with the following format. 

```
Program title
Program description


[ACTION_NAME] arg1 arg2
[ACTION_NAME] arg1 arg2
...
```
Where each argument has the format `<OBJECT_NAME> (ID_OBJECT)`. The number of arguments depends on the action type. The programs can also have a precondition file, specifying the state of the objects before the program is executed.

You can view the supported actions, objects and preconditions in [Resources]().

