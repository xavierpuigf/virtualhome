from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import numpy as np
import matplotlib.pyplot as plt
import PIL
import numpy as np

import plotly.plotly as py
import plotly.graph_objs as go

import networkx as nx


def fake_bb(ax):
    ax.set_aspect('equal')
    X = np.array([-10,5])
    Y = np.array([-10, 5])
    Z = np.array([-1, 6])

    #scat = ax.scatter(X, Y, Z)

    # Create cubic bounding box to simulate equal aspect ratio
    max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max()
    Xb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(X.max()+X.min())
    Yb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(Y.max()+Y.min())
    Zb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(Z.max()+Z.min())
    # Comment or uncomment following both lines to test the fake bounding box:
    for xb, yb, zb in zip(Xb, Yb, Zb):
       ax.plot([xb], [yb], [zb], 'w')

def cuboid(ax, coords, sides):
    points = []
    vertices = [[
        (coords[0]-sides[0]/2., coords[2]-sides[2]/2., coords[1]-sides[1]/2.),
        (coords[0]+sides[0]/2., coords[2]-sides[2]/2., coords[1]-sides[1]/2.),
        (coords[0]+sides[0]/2., coords[2]+sides[2]/2., coords[1]-sides[1]/2.),
        (coords[0]-sides[0]/2., coords[2]+sides[2]/2., coords[1]-sides[1]/2.),

    ]]
    # x = [v[0] for v in vertices]
    # y = [v[1] for v in vertices]
    # z = [v[2] for v in vertices]
    
    faces = Poly3DCollection(vertices, linewidths=0.2, alpha=0.3)
    face_color = [0.5, 0.5, 1] # alternative: matplotlib.colors.rgb2hex([0.5, 0.5, 1])
    faces.set_facecolor(face_color)
    ax.add_collection(faces)

    #ax.add_collection3d(Line3DCollection(vertices, colors='k', linewidths=0.2, linestyles=':'))

    return faces


def get_xyz_mouse_click(event, ax):
    """
    Get coordinates clicked by user
    """
    if ax.M is None:
        return {}

    xd, yd = event.xdata, event.ydata
    p = (xd, yd)
    edges = ax.tunit_edges()
    ldists = [(mplot3d.proj3d.line2d_seg_dist(p0, p1, p), i) for \
                i, (p0, p1) in enumerate(edges)]
    ldists.sort()

    # nearest edge
    edgei = ldists[0][1]

    p0, p1 = edges[edgei]

    # scale the z value to match
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    d0 = np.hypot(x0-xd, y0-yd)
    d1 = np.hypot(x1-xd, y1-yd)
    dt = d0+d1
    z = d1/dt * z0 + d0/dt * z1

    x, y, z = mplot3d.proj3d.inv_transform(xd, yd, z, ax.M)
    return x, y, z

def display(graph):
    nodes = graph['nodes']
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.set_aspect('equal')
    fake_bb(ax)
    xdata = []
    ydata = []
    colors = []
    color2id = {}
    color2points = {}
    zdata = []
    for node in nodes:
        cat_name = node['category'].lower().strip()
        
        if cat_name in ['floor', 'floors', 'ceiling',
                        'walls', 'windows', 'doors', 'light']:
            continue

        bbox = node['bounding_box']
        if node['category'] == 'Rooms':
            faces = cuboid(ax, bbox['center'], bbox['size'])
            
    
        else:
            
            if cat_name not in color2id.keys():
                color2id[cat_name] = len(color2id)
                color2points[cat_name] = []
            ct = bbox['center']
            color2points[cat_name].append(ct)
            
            colors.append(color2id[cat_name])

    for cat_name in color2id.keys():
        xdata = [x[0] for x in color2points[cat_name]]
        ydata = [x[2] for x in color2points[cat_name]]
        zdata = [x[1] for x in color2points[cat_name]]
        ax.scatter3D(xdata, ydata, zdata, label=cat_name, cmap=plt.cm.jet, picker=True)
    
    annot = ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)
    ax.axis('equal')
    ax.legend()
    text=ax.text(0,0,0,"", va="bottom", ha="left")
    def on_press(event):
        print('EVENT')
        x,y,z = simple_pick_info.pick_info.get_xyz_mouse_click(event, ax)    
        text.set_text('aAA')

    cid = fig.canvas.mpl_connect('pick_event', on_press)


    #fig.canvas.mpl_connect("motion_notify_event", hover)


# def draw_plot(graph):
#     G = nx.Graph()
#     G.add_nodes_from(graph['nodes'])

#     edge_trace = go.Scatter(
#         x=[],
#         y=[],
#         line=dict(width=0.5,color='#888'),
#         hoverinfo='none',
#         mode='lines')
#     for edge in G.edges():
#         x0, y0 = G.node[edge[0]]['pos']
#         x1, y1 = G.node[edge[1]]['pos']
#         edge_trace['x'] += tuple([x0, x1, None])
#         edge_trace['y'] += tuple([y0, y1, None])


#     node_trace = go.Scatter(
#     x=[],
#     y=[],
#     text=[],
#     mode='markers',
#     hoverinfo='text',
#     marker=dict(
#         showscale=True,
#         # colorscale options
#         #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
#         #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
#         #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
#         colorscale='YlGnBu',
#         reversescale=True,
#         color=[],
#         size=10,
#         colorbar=dict(
#             thickness=15,
#             title='Node Connections',
#             xanchor='left',
#             titleside='right'
#         ),
#         line=dict(width=2)))

#     for node in G.nodes():
#         x, y = G.node[node]['pos']
#         node_trace['x'] += tuple([x])
#         node_trace['y'] += tuple([y])
#         node_trace['marker']['color']+=([5])

    
#     fig = go.Figure(data=[edge_trace, node_trace],
#              layout=go.Layout(
#                 titlefont=dict(size=16),
#                 showlegend=False,
#                 hovermode='closest',
#                 margin=dict(b=20,l=5,r=5,t=40),
#                 annotations=[ dict(
#                     text="Python code: <a href='https://plot.ly/ipython-notebooks/network-graphs/'> https://plot.ly/ipython-notebooks/network-graphs/</a>",
#                     showarrow=False,
#                     xref="paper", yref="paper",
#                     x=0.005, y=-0.002 ) ],
#                 xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#                 yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

#     py.iplot(fig, filename='networkx')
