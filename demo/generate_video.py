# Generate video for a program. Make sure you have the executable open
import sys
sys.path.append('../simulation/')
from unity_simulator.comm_unity import UnityCommunication
script = ['[Walk] <sofa> (1)', '[Sit] <sofa> (1)'] # Add here your script
print('Starting Unity...')
comm = UnityCommunication()
print('Starting scene...')
comm.reset()
print('Generating video...')
comm.render_script(script, capture_screenshot=True, processing_time_limit=60)
print('Generated, find video in simulation/unity_simulator/output/')
