# compas_cloud
compas_cloud is the further development of `compas.rpc` module. It uses websocktes instead of RESTful APIs to allow bi-directional communications between various front-end programs like Rhino, GH, RhinoVault2, blender or web-based viewers that are implemented in different enviroments including CPython, IronPython and Javascript. It also allows to save certain variables to backend inside a user session to avoid overheads created by redundant data transfers.



### Install from source
`pip install -e .`


### Install for Rhino
`python -m compas_rhino.install -p compas_cloud`


### Run examples
a benchmark test comparing pure python and numpy with remote    
`python examples/benchmark.py`

iterative plotting example with callbacks    
`python examples/dr_numpy.py`

using non-compas packages like numpy in ironpython  
`run examples/example_numpy.py with Rhino`

### Start server from command line
`python -m compas_cloud.server`  
(The proxy will automatically start a server in background if there isn't one to connect to)