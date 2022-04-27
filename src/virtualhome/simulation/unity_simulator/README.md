# Unity Simulator
## Quickstart
To start running the simulator, make sure the Unity Executable is running (use the desktop version or docker). If using the desktop version, make sure you select windowed and run **Play!** as shown in the screenshot.

<img src="../../assets/simulator.png" width=70%>

You can now run the simulator with the python API. Start the communication with the executable:

```python
from comm_unity import UnityCommunication
comm = UnityCommunication()
```

Render a simple video, saved in [output](output) folder.

```python
comm.reset()
script = [
	'[Walk] <chair> (1)',
	'[Sit] <chair> (1)'
]
comm.render_script(script)

```


Check the notebook [demo](../../demo/unity_demo.ipynb) to further explore the simulator.

