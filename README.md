# VirtualHome
VirtualHome is a platform to simulate complex household activities via Programs. 
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
- Dataset 
- Installation
- QuickStart
- Generating Videos/Keyframes
- Script Augmentation
- Other details

## Motivation

Among lots of simulator aiming at interacting with environments, why does virtualhome stand out? 
(can be that we focus on high-level action, including watching, ... etc.)

## Dataset

We collected a dataset of programs to execute in the environment. You can download them in [link to programs](). 
Once downloaded, move programs into the `dataset` folder. The dataset should follow the following structure:

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

Where `withoutconds` and `initstate` contain the original programs and pre-conditions. 

To view a script executed in an enviornment, check `executable_programs/{environment}/{script_name}.txt`. 

To view the graph of the environment throughout the script execution of a program, check   `state_list/{environment}/{script_name}.json`.

To check how the environments and sripts look like, check [dataset/README.md](dataset/README.md) for detailed information.

## Installation

How to install the executable or run the code in Unity
### Step 1
Download the virtualhome simulator.

- [Download]() UNIX version
- [Download]() MacOSX version.

### Step 2

Clone this repository
```bash
git clone https://mboben@bitbucket.org//virtualhome.git
# and maybe some basic setup
# and download the original scripts
```


## QuickStart

Run `sh run_example.sh` and you will get an activity video of this [scripts](example_scripts/...). 
You can check more example activity videos [here]().

For more details, see `example.py` file and there are some example scripts in `example_scripts` folder


## Genrating Videos/Keyframes

VirtualHome allows generating videos corresponding to an activity and keyframes corresponding to a snapshot of the environment state.


### Generate videos


If you want to generate the videos of the given scripts, 
```bash
```

### Generate keyframes

If you want to generate the keyframes of the given scripts, 
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


## Docker
You can also run VirtualHome using Docker. You can find how to set it up [here](Docker)

