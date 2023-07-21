# Generate video for a program. Make sure you have the executable open
import sys

sys.path.append('../simulation')
from unity_simulator.comm_unity import UnityCommunication


script = ['<char0> [Walk] <tv> (1)', '<char0> [switchon] <tv> (1)', '<char0> [Walk] <sofa> (1)', '<char0> [Sit] <sofa> (1)', '<char0> [Watch] <tv> (1)'] # Add here your script

print('Starting Unity...')
comm = UnityCommunication()

print('Starting scene...')
comm.reset()
comm.add_character('Chars/Female1')

print('Generating video...')
comm.render_script(script, recording=True, find_solution=True)

print('Generated, find video in simulation/unity_simulator/output/')
