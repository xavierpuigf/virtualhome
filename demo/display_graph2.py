import json
import os

import pdb
import plotly.graph_objects as go

import plotly.graph_objects as go
import plotly.io
import pdb
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import plotly.offline


dict_info = {
    "objects_inside": [
        "toilet", "bathroom_cabinet", "kitchencabinets",
        "bathroom_counter", "kitchencounterdrawer", "cabinet", "fridge", "oven", "dishwasher", "microwave"],

    "objects_surface": ["bathroomcabinet",
                        "bathroomcounter",
                        "bed",
                        "bench",
                        "boardgame",
                        "bookshelf",
                        "cabinet",
                        "chair",
                        "coffeetable",
                        "cuttingboard",
                        "desk",
                        "fryingpan",
                        "kitchencabinets",
                        "kitchencounter",
                        "kitchentable",
                        "mousemat",
                        "nightstand",
                        "oventray",
                        "plate",
                        "radio",
                        "sofa",
                        "stove",
                        "towelrack"],
    "objects_grab": [
        "pudding", "juice", "pancake", "apple",
        "book", "coffeepot", "cupcake", "cutleryfork", "dishbowl", "milk",
        "milkshake", "plate", "poundcake", "remotecontrol", "waterglass", "wine", "wineglass", "pillow"
    ]
}


def create_cube(n, color='lightpink', opacity=0.1, cont=False):
    c, b = n['bounding_box']['center'], n['bounding_box']['size']

    if cont:
        xp = [c[0] - b[0] / 2., c[0] + b[0] / 2.] * 4
        zp = [c[1] - b[1] / 2.] * 4 + [c[1] + b[1] / 2.] * 4
        yp = [c[2] - b[2] / 2.] * 2 + [c[2] + b[2] / 2.] * 2 + [c[2] - b[2] / 2.] * 2 + [c[2] + b[2] / 2.] * 2
        indices = [0, 1, 3, 2, 0, 4, 5, 1, 5, 7, 3, 7, 6, 2, 6, 4]
        x = [xp[it] for it in indices]
        y = [yp[it] for it in indices]
        z = [zp[it] for it in indices]
        cube_data = go.Scatter3d(x=x, y=y, z=z, showlegend=False, opacity=opacity, mode='lines', hoverinfo='skip',
                                 marker={'color': color})
    else:
        x = [c[0] - b[0] / 2., c[0] + b[0] / 2.] * 4
        z = [c[1] - b[1] / 2.] * 4 + [c[1] + b[1] / 2.] * 4
        y = [c[2] - b[2] / 2.] * 2 + [c[2] + b[2] / 2.] * 2 + [c[2] - b[2] / 2.] * 2 + [c[2] + b[2] / 2.] * 2
        i = [0, 3, 4, 7, 0, 6, 1, 7, 0, 5, 2, 7]
        j = [1, 2, 5, 6, 2, 4, 3, 5, 4, 1, 6, 3]
        k = [3, 0, 7, 4, 6, 0, 7, 1, 5, 0, 7, 2]
        cube_data = go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity)
    return cube_data


def create_points(nodes, color='red'):
    centers = [n['bounding_box']['center'] for n in nodes]
    class_and_ids = ['{}.{}'.format(node['class_name'], node['id']) for node in nodes]
    x, z, y = zip(*centers)
    scatter_data = go.Scatter3d(x=x, y=y, z=z, mode='markers', marker={'size': 3, 'color': color},
                                showlegend=False, hovertext=class_and_ids)
    return scatter_data


def plot_graph(graph, char_id=1, visible_ids=None, action_ids=None):
    nodes_interest = [node for node in graph['nodes'] if 'GRABBABLE' in node['properties']]
    container_surf = dict_info['objects_inside'] + dict_info['objects_surface']
    container_and_surface = [node for node in graph['nodes'] if node['class_name'] in container_surf]
    grabbed_obj = [node for node in graph['nodes'] if node['class_name'] in dict_info['objects_grab']]
    rooms = [node for node in graph['nodes'] if 'Rooms' == node['category']]

    # Character
    # char_node = [node for node in graph['nodes'] if node['id'] == char_id][0]

    room_data = [create_cube(n, color='lightpink', cont=True, opacity=0.9) for n in rooms]

    # containers and surfaces
    # visible_nodes = [node for node in graph['nodes'] if node['id'] in visible_ids]
    # action_nodes = [node for node in graph['nodes'] if node['id'] in action_ids]

    goal_nodes = [node for node in graph['nodes'] if node['class_name'] == 'cupcake']
    object_data2 = [create_cube(n, color='green', cont=True, opacity=0.3) for n in grabbed_obj]
    object_data = [create_cube(n, color='blue', cont=True, opacity=0.1) for n in container_and_surface]
    # object_data_vis = [create_cube(n, color='green', cont=True, opacity=0.2) for n in visible_nodes]
    # object_data_action = create_points(action_nodes, color='pink')

    fig = go.Figure()

    # fig.add_traces(data=create_cube(char_node, color="yellow", opacity=0.8))
    fig.add_traces(data=object_data)
    fig.add_traces(data=object_data2)
    # fig.add_traces(data=object_data_vis)
    # fig.add_traces(data=object_data_action)
    fig.add_traces(data=room_data)
    # fig.add_traces(data=create_points(goal_nodes))

    fig.update_layout(scene_aspectmode='data')
    return fig


def save_graph(graph, char_id=1, visible_ids=None, action_ids=None):
    fig = plot_graph(graph, char_id, visible_ids, action_ids)
    html_str = plotly.io.to_html(fig, include_plotlyjs=False, full_html=False)
    return html_str

#
# if __name__ == '__main__':
#     import json
#
#     with open('graph_seq2.json', 'r') as f:
#         graphs = json.load(f)
#     return_str = save_graph(graphs[0])
#     pdb.set_trace()



##### 2D PLOTTING ####

def get_bounds(bounds):
    minx, maxx = None, None
    miny, maxy = None, None
    for bound in bounds:
        bgx, sx = bound['center'][0] + bound['size'][0] / 2., bound['center'][0] - bound['size'][0] / 2.
        bgy, sy = bound['center'][2] + bound['size'][2] / 2., bound['center'][2] - bound['size'][2] / 2.
        minx = sx if minx is None else min(minx, sx)
        miny = sy if miny is None else min(miny, sy)
        maxx = bgx if maxx is None else max(maxx, bgx)
        maxy = bgy if maxy is None else max(maxy, bgy)
    return (minx, maxx), (miny, maxy)


def add_box(nodes, args_rect):
    rectangles = []
    centers = [[], []]
    for node in nodes:
        cx, cy = node['bounding_box']['center'][0], node['bounding_box']['center'][2]
        w, h = node['bounding_box']['size'][0], node['bounding_box']['size'][2]
        minx, miny = cx - w / 2., cy - h / 2.
        centers[0].append(cx)
        centers[1].append(cy)
        if args_rect is not None:
            rectangles.append(
                Rectangle((minx, miny), w, h, **args_rect)
            )
    return rectangles, centers


def add_boxes(nodes, ax, points=None, rect=None):
    rectangles = []
    rectangles_class, center = add_box(nodes, rect)
    rectangles += rectangles_class
    if points is not None:
        ax.scatter(center[0], center[1], **points)
    if rect is not None:
        ax.add_patch(rectangles[0])
        collection = PatchCollection(rectangles, match_original=True)
        ax.add_collection(collection)


def plot_graph_2d(graph, char_id, visible_ids, action_ids, goal_ids):


    #nodes_interest = [node for node in graph['nodes'] if 'GRABBABLE' in node['properties']]
    goals = [node for node in graph['nodes'] if node['id'] in goal_ids]
    container_surf = dict_info['objects_inside'] + dict_info['objects_surface']
    container_and_surface = [node for node in graph['nodes'] if node['class_name'] in container_surf]

    #grabbed_obj = [node for node in graph['nodes'] if node['class_name'] in dict_info['objects_grab']]
    rooms = [node for node in graph['nodes'] if 'Rooms' == node['category']]


    # containers and surfaces
    visible_nodes = [node for node in graph['nodes'] if node['id'] in visible_ids and node['category'] != 'Rooms']
    action_nodes = [node for node in graph['nodes'] if node['id'] in action_ids and node['category'] != 'Rooms']

    goal_nodes = [node for node in graph['nodes'] if node['class_name'] == 'cupcake']

    # Character
    char_node = [node for node in graph['nodes'] if node['id'] == char_id][0]

    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes()
    add_boxes(rooms, ax, points=None, rect={'alpha': 0.1})
    add_boxes(container_and_surface, ax, points=None, rect={'fill': False,
                                                                        'edgecolor': 'blue', 'alpha': 0.3})
    add_boxes([char_node], ax, points=None, rect={'facecolor': 'yellow', 'edgecolor': 'yellow', 'alpha': 0.7})
    add_boxes(visible_nodes, ax, points={'s': 2.0, 'alpha': 1.0}, rect={'fill': False,
                                                                         'edgecolor': 'green', 'alpha': 1.0})
    add_boxes(goals, ax, points={'s':  100.0, 'alpha': 1.0, 'edgecolors': 'orange', 'facecolors': 'none', 'linewidth': 3.0})
    add_boxes(action_nodes, ax, points={'s': 3.0, 'alpha': 1.0, 'c': 'red'})


    bad_classes = ['character']

    ax.set_aspect('equal')
    bx, by = get_bounds([room['bounding_box'] for room in rooms])

    maxsize = max(bx[1] - bx[0], by[1] - by[0])
    gapx = (maxsize - (bx[1] - bx[0])) / 2.
    gapy = (maxsize - (by[1] - by[0])) / 2.

    ax.set_xlim(bx[0]-gapx, bx[1]+gapx)
    ax.set_ylim(by[0]-gapy, by[1]+gapy)
    ax.apply_aspect()
    return fig

def save_graph_2d(img_name, graph, visible_ids, action_ids, goal_ids, char_id=1):
    fig = plot_graph_2d(graph, char_id, visible_ids, action_ids, goal_ids)
    # plt.axis('scaled')
    fig.tight_layout()


    fig.savefig(img_name)
    plt.close(fig)



####################


def render(el):
    if el is None:
        return "None"
    if type(el) == list:
        ncontent = [x.replace('<', '&lt').replace('>', '&gt').replace('[', '&lbrack;').replace(']', '&rbrack;') for x in el]
        return ''.join(['<span style="display:inline-block; width: 150px">'+x+'</span>' for x in ncontent])
    if type(el) == str:
        el_html = el.replace('<', '&lt').replace('>', '&gt').replace('[', '&lbrack;').replace(']', '&rbrack;')
        return el_html
    if type(el) == dict:
        visible_ids = el['visible_ids'][0]
        action_ids = [t for t in el['action_ids'][0] if t in visible_ids]

        return save_graph(el['graph'][0], visible_ids=visible_ids, action_ids=action_ids)
    else:
        return el.render()

class html_img:
    def __init__(self, src):
        self.src = src

    def render(self):
        return '<img src="{}" style="height: 600px">'.format(self.src)

def html_table(titles, max_rows, column_info, column_style=None):
    header = ''.join(['<th>{}</th>'.format(title) for title in titles])
    table_header = '<tr> {} </tr>'.format(header)

    table_contents = ''
    widths = column_style

    for row_id in range(max_rows):
        table_contents += '<tr>'
        for it in range(len(column_info)):
            if widths is not None:
                w = widths[it]
            else:
                w = ''
            if len(column_info[it]) > row_id:
                el = column_info[it][row_id]
                table_contents += '<td style="{}"> {} </td>'.format(w, render(el))
            else:
                table_contents += '<td style="{}"></td>'.format(w)
        table_contents += '</tr>'
    table_ep = '<table style="border-width: 2px; color: black; border-style: solid" > {} {} </table>'.format(table_header, table_contents)
    return table_ep


