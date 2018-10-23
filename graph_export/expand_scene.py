from graph_export.scriptcheck import UnityCommunication
import json
from PIL import Image


def expand_scene():
    comm = UnityCommunication()
    with open('../test_graphs_for_model/file1002_1_250.json', 'r') as f:
        graph_list = json.load(f)
        comm.reset()
        success, message = comm.expand_scene(graph_list['graph_state_list'][0])
        print("Expanding scene: ", success)
        if not success:
            print(message)
        else:
            success, value = comm.camera_count()
            print("Cameras: ", value)
            success, imgs = comm.camera_image([0,1,2,38])
            for i, img in enumerate(imgs):
                img.save('c:/tmp/camera_img_{0:03d}.jpg'.format(i))


if __name__ == '__main__':
    expand_scene()
