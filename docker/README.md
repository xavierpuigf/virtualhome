

# Docker
You can also run VirtualHome using Docker, avoiding installing OpenGL and Xvfb. This setup is based on [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents).

## Requirements
- [Docker](https://www.docker.com/)

## Setup
Run 
```
sh prepare_docker.sh
```
It will download the Unity Simulator and put it in a `unity_vol` folder, where videos will be stored when running the simulator on Docker.

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
