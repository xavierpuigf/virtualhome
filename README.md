# VirtualHome
VirtualHome is a platform to simulate complex household activities via programs. 
Given an initial environment describing an apartment and a program depicting a sequence of actions, 
VirtualHome executes the program generating a video of the activity together with useful data for activity understanding or planning.

Check out more details of the environmnent and platform in [VirtualHome](http://virtual-home.org). 

![intro](/assets/vh_intro.gif)


## Cite VirtualHome

VirtualHome has been used in:

- VirtualHome: Simulating HouseHold Activities via Programs, CVPR2018
- Synthesizing Environment-Aware Activities via Activity Sketches, CVPR2019


```
@inproceedings{puig2018virtualhome,
  title={Virtualhome: Simulating household activities via programs},
  author={Puig, Xavier and Ra, Kevin and Boben, Marko and Li, Jiaman and Wang, Tingwu and Fidler, Sanja and Torralba, Antonio},
  booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},
  pages={8494--8502},
  year={2018}
}
```

```
@inproceedings{puig2018virtualhome,
  title={Virtualhome: Simulating household activities via programs},
  author={Puig, Xavier and Ra, Kevin and Boben, Marko and Li, Jiaman and Wang, Tingwu and Fidler, Sanja and Torralba, Antonio},
  booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},
  pages={8494--8502},
  year={2018}
}
```

## Contents

- Motivation
- Overview
- Dataset 
- Set Up
- Generating Videos/Keyframes
- Script Augmentation
- Other details

## Motivation

Among lots of simulator aiming at interacting with environments, why does virtualhome stand out? 
(can be that we focus on high-level action, including watching, ... etc.)

## Overview
Activities in VirtualHome are represented through two components: *programs* representing the sequence of actions that compose an activity, and *graphs* representing a definition of the environment where the activity takes place. Given a program and a graph, the simulator executes the program, generating a video of the activity or a sequence of graphs representing how the environment evolves as the activity takes place. To this end, VirtualHome includes two simulators: the Unity simulator and EvolvingGraph.

#### Unity Simulator 
This simulator is built in Unity and allows to generate videos of activities. To use this simulator you will need to download the appropiate executable and run the [simulation/unity_simulator/comm_unity.py](simulation/unity_simulator/comm_unity.py) API.

#### Evolving Graph
This simulator runs fully in python and allows to generate a sequence of graphs when a program is executed. You can run it in [simulation/evolving_graph](evolving_graph). Note that some of the objects and actions in this simulator are not supported yet in Unity Simulator.


## Dataset

We collected a dataset of programs and augmented them with graphs using the Evolving Graph simulator. You can download them [here - GET LINK](). 
Once downloaded, move the programs into the `dataset` folder. The dataset should follow the following structure:

```
dataset
└── programs_processed_precond_nograb_morepreconds
	|── initstate
	├── withoutconds
	├── executable_programs
	|   ├── TrimmedTestScene7_graph
	|	└── ...
	└── state_list
		├── TrimmedTestScene7_graph
	   	└── ...	
```

The folders `withoutconds` and `initstate` contain the original programs and pre-conditions. 

When a script is executed in an environment, the script changes by aligning the original objects with instances in the environment. You can view the resulting script in `executable_programs/{environment}/{script_name}.txt`.

To view the graph of the environment, and how it changes throughout the script execution of a program, check   `state_list/{environment}/{script_name}.json`.

You can find more details of the programs and environment graphs in [dataset/README.md](dataset/README.md). 


## Set Up

How to install the executable or run the code in Unity

### Clone repository and install dependencies
```bash
git clone https://mboben@bitbucket.org//virtualhome.git
# and maybe some basic setup
# and download the original scripts
```

### Download UnitySimulator
Download the VirtualHome UnitySimulator executable and move it under `simulation/unity_simulator`.

- [Download]() Linux x86-64 version.
- [Download]() Mac OS X version.


### Test simulator

To test the UnitySimulator, double click the executable and select a resolution and screen size. Then, run the `sh run_example.sh` and you will get an activity video of this [scripts](example_scripts/...). 
You can further check the UnitySimulator by running the demo notebook in `demo/unity_demo.ipynb`.

You can also test the EvolvingGraph simulator in `link`. Note that this simulator does not require opening any executable.

### Docker
You can also run UnitySimulator using Docker. You can find how to set it up [here](Docker).


## Generating Videos and Snapshots

VirtualHome UnitySimulator allows generating videos corresponding to household activities. In addition, it is possible to use EvolvingGraph simulator to obtain the environment for each execution step and use UnitySimulator to generate snapshots of the environment at each step.


### Generate videos

Open the simulator as indicated in [Test simulator](###Test simulator). And go to directory `simulation/unity_simulator/`. Then run:

```bash
from comm_unity import UnityCommunication
script = ['[Walk] <sofa> (1)', '[Sit] <sofa> (1)'] # Add here your script
comm = UnityCommunication()
comm.reset()
comm.render_script(script, capture_screenshot=True)

```
The video frames will be generated in a folder called `output`. You can check more options in the [demo](demo/unity_demo.ipynb).


### Generate snapshots

To generate snapshots. Open the simulator as indicated in [Test simulator](###Test simulator).

```bash
# commands of generating keyframes
```

## Script Augmentation


In *Synthesizing Environment-Aware Activities via Activity Sketches*, 
we augment the scripts with two knowledge base `KB-RealEnv` and `KB-ExceptonHandler`.
You can download the augmented scripts [here]().

Here, we provide the code to augment the sripts:

### Augment with `KB-Affordance`

```bash
cd dataset_generation
python augment_dataset_affordances.py
```
Note that this is not used in *Synthesizing Environment-Aware Activities via Activity Sketches*.

### Augment with `KB-RealEnv`

```bash
cd dataset_generation
python augment_dataset_locations.py
```


### Augment with `KB-ExceptionHandler`

```bash
cd dataset_generation
python augment_dataset_exceptions.py
```

## Resources

To do the above generation and augmentation, some valuable resource files are used to set the properties of objects, set the affordance of objects, etc.
Check [resources/README.md](resources/README.md) for more details.




