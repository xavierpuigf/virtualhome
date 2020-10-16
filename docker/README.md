

# Docker
You can also run VirtualHome using Docker, avoiding installing OpenGL and Xvfb. This setup is based on [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents).

## Requirements
- [Docker](https://www.docker.com/)

## Setup
- [Download](http://wednesday.csail.mit.edu/frames/data_acquisition/SyntheticStories/release/simulator/linux_sim.zip) the VirtualHome exectable for Linux.
- [Download](https://www.docker.com/) and install Docker if you don't have it setup on your machine.
- Create a directory `unity_vol` with all write permissions and add the executable inside.

## Usage
### Build the Docker Container
First, make sure the Docker engine is running on your machine. Then build the Docker container by calling the following command at the top-level of the repository:
```
docker build -t <image-name> .
```
Replace <image-name> with a name for the Docker image.
### Run the Docker container
Run the Docker container by calling the following command at the top-level of the repository:

```
docker run --mount type=bind,source="$(pwd)"/unity_vol,target=/unity_vol/ \
 			 -p 8080:8080 \
 			 -ti <container-name> \
```
Where you can replace `8080` by your port of preference.
The Docker will start the simulator. You can now run the api in the same machine and get the output images.
