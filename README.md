# VirtualHome
VirtualHome is a platform to simulate complex household activities via Programs. Given an initial environment describing an apartment and a program depicting a sequence of actions, VirtualHome executes the program generating a video of the activity together with useful data for activity understanding or planning.

Check out more details of the environmnent and platform in [virtualhome.org](). VirtualHome has been used in:

- VirtualHome: Simulating HouseHold Activities via Programs
- Synthesizing Environment-Aware Activities via Activity Sketches

# Dependencies

```
Write here the dependencies
```

# QuickStart
Clone the repository and download the simulator

```
git clone https://mboben@bitbucket.org//virtualhome.git
instructions to copy the executable
```

Run `sh run_example.sh` to generate an example activity video. You can find the generated video in `folder_name`. You can check more examples [here]().



## Contents
### Examples

For how to use the code, see `example.py` file.
Example scripts are located in `example_scripts` folder

### Environment
VirtualHome is composed of 7 apartments where activities can be executed. Each apartment is encoded in a json file containing a node for every object and edges between them representing relationships. Each apartment can be modified through the corresponding json file. The files representing each apartment can be found in `example_graphs`. Check `example_scripts/` for examples on how to read and update graphs.

### Data
We collected a dataset of programs to execute in the environment. You can download the programs in [link to programs](). The videos generated from these programs can be found in [link to videos](). 

The data follows the following structure

```
programs_processed_precond_nograb_morepreconds/
|── initstate
├── withoutconds
├── executable_programs
   	├── TrimmedTestScene7_graph
	├── ...
└── state_list
	├── TrimmedTestScene7_graph
     ├── ...

```

Where `withoutconds` and `initstate` contain the original programs and pre-conditions. Each program is executed in one environment.  `state_list` contains the environment state throughout the execution of the program.

#### Script generation
Each program is executed differently depending on the initial environment. 



#### Script augmentation

The original programs can be extended by replacing objects or perturbating the environment. You can find more details about how it is extended in [our paper](). To augment the dataset run.

```
cd dataset_generation
python augment_dataset_affordances.py
python augment_dataset_locations.py

```  


### Videos
The generated videos will be saved in the folder. Each video has the following contents

```
programs_processed_precond_nograb_morepreconds/
|── initstate
├── withconds
└── withoutconds
```

### Rules
In `rules_doc`, you can find the currently implemented actions, their preconditions and post-conditions.   


## Dataset generation

### dataset structure

programs_processed_precond_nograb_morepreconds/
├── initstate
├── withconds
└── withoutconds

- go to dataset_augmentation/ and run `python augment_dataset_affordances.py`
- run `python augment_dataset_locations.py`
- go to root dir, and run `python check_programs.py` with check_2('dataset_augmentation/augmented_location_augmented_affordance_programs_processed_precond_nograb_morepreconds', graph_path=translated_path)
- got o dataset_augmentation/ and run `python perturbate_dataset.py`
- go to root dir, and run `python check_programs.py` with check_2('dataset_augmentation/perturb_augmented_location_augmented_affordance_programs_processed_precond_nograb_morepreconds', graph_path=translated_path)

 

### Resources
Contains resource files used to initialize the environment, set properties of objects and generate videos given the scripts. Check the folder for a description of its contents.

Folder `resources` contains json files with information about:

