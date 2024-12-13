import glob
import sys
from sys import platform

# Needs to be fixed!
original_path = sys.path[5]
new_path = original_path + '/virtualhome/simulation'
sys.path.append(new_path)

# if installed via pip
try:
    from unity_simulator.comm_unity import UnityCommunication
    from unity_simulator import utils_viz

# if running locally (cloned into the project repository)
except ModuleNotFoundError:
    from .simulation.unity_simulator.comm_unity import UnityCommunication
    from .simulation.unity_simulator import utils_viz
