from graph_export.scriptcheck import UnityCommunication
import json


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
            success, imgs = comm.camera_image(38, mode='seg_inst')
            # Possible modes are: 'normal', 'seg_inst', 'seg_class', 'depth', 'flow'
            if success:
                imgs[0].save('c:/tmp/camera_img_{0:03d}.jpg'.format(38))
            success, imgs = comm.camera_image([39, 40])
            if success:
                imgs[0].save('c:/tmp/camera_img_{0:03d}.jpg'.format(39))
                imgs[1].save('c:/tmp/camera_img_{0:03d}.jpg'.format(40))


if __name__ == '__main__':
    expand_scene()
