import random

import compas
from compas.datastructures import Mesh
from compas_plotters import MeshPlotter
from compas.utilities import i_to_rgb
from compas.numerical import dr_numpy


from compas_cloud import Proxy
p = Proxy()
dr_cloud = p.package('compas.numerical.dr_numpy')

dva = {
    'is_fixed': False,
    'x': 0.0,
    'y': 0.0,
    'z': 0.0,
    'px': 0.0,
    'py': 0.0,
    'pz': 0.0,
    'rx': 0.0,
    'ry': 0.0,
    'rz': 0.0,
}

dea = {
    'qpre': 1.0,
    'fpre': 0.0,
    'lpre': 0.0,
    'linit': 0.0,
    'E': 0.0,
    'radius': 0.0,
}

mesh = Mesh.from_obj(compas.get('faces.obj'))

mesh.update_default_vertex_attributes(dva)
mesh.update_default_edge_attributes(dea)

for key, attr in mesh.vertices(True):
    attr['is_fixed'] = mesh.vertex_degree(key) == 2

for u, v, attr in mesh.edges(True):
    attr['qpre'] = 1.0 * random.randint(1, 7)

k_i = mesh.key_index()

vertices = mesh.get_vertices_attributes(('x', 'y', 'z'))
edges    = [(k_i[u], k_i[v]) for u, v in mesh.edges()]
fixed    = [k_i[key] for key in mesh.vertices_where({'is_fixed': True})]
loads    = mesh.get_vertices_attributes(('px', 'py', 'pz'))
qpre     = mesh.get_edges_attribute('qpre')
fpre     = mesh.get_edges_attribute('fpre')
lpre     = mesh.get_edges_attribute('lpre')
linit    = mesh.get_edges_attribute('linit')
E        = mesh.get_edges_attribute('E')
radius   = mesh.get_edges_attribute('radius')

lines = []
for u, v in mesh.edges():
    lines.append({
        'start': mesh.vertex_coordinates(u, 'xy'),
        'end'  : mesh.vertex_coordinates(v, 'xy'),
        'color': '#cccccc',
        'width': 0.5
    })

plotter = MeshPlotter(mesh, figsize=(10, 7), fontsize=6)

plotter.draw_lines(lines)
plotter.draw_vertices(facecolor={key: '#000000' for key in mesh.vertices_where({'is_fixed': True})})
plotter.draw_edges()

plotter.update(pause=1.0)

import numpy as np

def callback(k, xyz, crits, args):
    print(k)

    plotter.update_vertices()
    plotter.update_edges()
    plotter.update(pause=0.001)

    for key, attr in mesh.vertices(True):
        index = k_i[key]
        attr['x'] = xyz[index][0]
        attr['y'] = xyz[index][1]
        attr['z'] = xyz[index][2]

# xyz, q, f, l, r = dr_numpy(vertices, edges, fixed, loads,
#                             qpre, fpre, lpre,
#                             linit, E, radius,
#                             kmax=100, callback=callback)

# print(xyz)

xyz, q, f, l, r = dr_cloud(vertices, edges, fixed, loads,
                            qpre, fpre, lpre,
                            linit, E, radius,
                            kmax=100, callback=callback)



for index, (u, v, attr) in enumerate(mesh.edges(True)):
    attr['f'] = f[index][0]
    attr['l'] = l[index][0]

fmax = max(mesh.get_edges_attribute('f'))

plotter.clear_vertices()
plotter.clear_edges()

plotter.draw_vertices(
    facecolor={key: '#000000' for key in mesh.vertices_where({'is_fixed': True})}
)

plotter.draw_edges(
    text={(u, v): '{:.0f}'.format(attr['f']) for u, v, attr in mesh.edges(True)},
    color={(u, v): i_to_rgb(attr['f'] / fmax) for u, v, attr in mesh.edges(True)},
    width={(u, v): 10 * attr['f'] / fmax for u, v, attr in mesh.edges(True)}
)

plotter.update(pause=1.0)
plotter.show()