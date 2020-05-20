# compas_cloud
compas_cloud is the further development of `compas.rpc` module. It uses websocktes instead of RESTful APIs to allow bi-directional communications between various front-end programs like Rhino, GH, RhinoVault2, blender or web-based viewers that are implemented in different enviroments including CPython, IronPython and Javascript. It also allows to save certain variables to backend inside a user session to avoid overheads created by redundant data transfers.

## Installation

### Install from source
```bash
git clone https://github.com/BlockResearchGroup/compas_cloud.git
pip install -e .
```


### Install for Rhino
```bash
python -m compas_rhino.install -p compas_cloud
```


## Using Proxy

### Running the sever:

1. Start from command line:
    ```bash
    python -m compas_cloud.server
    ```  
2. The proxy will automatically start a server in background if there isn't one to connect to. If the server is started this way, it will keep operating in background and reconnect if a new proxy is create later.

### Basic Usage
One of the main purposes of compas_cloud is to allow usage of full COMPAS functionalities in more closed envinroments like IronPython. The following example shows how to use a numpy based COMPAS function through a proxy which can be run in softwares like Rhino:  
[basic.py](examples/basic.py)
```python
from compas_cloud import Proxy
from compas.geometry import Translation


proxy = Proxy()
transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy')
# create a proxy funciton

pts = [[0,0,0], [1,0,0]]
T = Translation([100, 0, 0]).matrix
transform_points_numpy(pts, T) # call the function through proxy
print(result)
# will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]
```

### Caching
Compas_cloud allows to cache data or function outputs at server side instead of sending them to the front-end all the time. This can vastly improve the performance for long iterative operations that involves large amount of data inputs and outputs.

[caching.py](examples/caching.py)
```python
from compas_cloud import Proxy
from compas.geometry import Translation

# CACHING INPUT PARAMETERS

proxy = Proxy()
transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy')
# create a proxy funciton

pts = [[0,0,0], [1,0,0]]
pts_cache = proxy.cache(pts) # cache the object to server side and return its reference
print(pts_cache) # will print: {'cached': some_unique_id}

T = Translation([100, 0, 0]).matrix
result = transform_points_numpy(pts_cache, T) # call the function through proxy
print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]



# CACHING RETURNED DATA

transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy', cache=True)
# this function will now return a cache object instead of the actual data

pts = [[0,0,0], [1,0,0]]
pts_cache = proxy.cache(pts)
print(pts_cache) # will print: {'cached': some_unique_id}

T = Translation([100, 0, 0]).matrix
result_cache = transform_points_numpy(pts_cache, T) # call the function through proxy
print(result_cache) # will print: {'cached': some_unique_id}

result = proxy.get(result_cache) # fetch the actual data of the cache object
print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]
```

### Server control
User can `restart/check/shutdown` a connected server from proxy with commands in following example: [server_control.py](examples/server_control.py)
```python
from compas_cloud import Proxy
import time

print("\n starting a new Proxy and by default starts a server in background")
proxy = Proxy(background=True)
time.sleep(3)

print("\n restarting the background server and open a new one in a prompt console")
proxy.background = False
proxy.restart()
time.sleep(3)

print("\n check if the proxy is healthily connected to server")
print(proxy.check())
time.sleep(3)


print("\n shut the the server and quite the program")
proxy.shutdown()
time.sleep(3)
```


### Other Examples
A [benchmark test](examples/benchmark.py) comparing pure python and numpy with caching to transform 10k points for 100 times: 
```bash
python examples/benchmark.py
```

[Iterative plotting](examples/dr_numpy.py) example with callbacks:    
```bash
python examples/dr_numpy.py
```

[Using non-compas packages like numpy with IronPython](examples/example_numpy.py):  
run `examples/example_numpy.py` with Rhino


## Using Sessions (Currently only work with MacOS/Linux)
`Compas_cloud.Sessions` is a task-manager class that helps to execute a batch of long-lasting tasks such as FEA and DEM simulations. It creates a queue of tasks and a collection of workers to execute the tasks in parallel and save the program logs into each corresponding locations. `Sessions` can be run either locally or in a background server through `Proxy`.

### Examples

#### [Running Sessions Locally](examples/sessions_local.py):
```bash
python examples/sessions_local.py
```

```python
from compas_cloud import Sessions

# define a psuedo task that will take few seconds to finish
def func(a):
    import time

    for i in range(a):
        time.sleep(1)
        print('sleeped ', i, 's')

# initiate a session object, and specify where the logs will be stored and number of workers
# if no log_path is given, all logs will be streamed to terminal and not saved
# the default worker_num is equal to the number of cpus accessible on the computer
s = Sessions(log_path=None, worker_num=4)

# add several tasks to the session using different parameters
s.add_task(func, 1)
s.add_task(func, 2)
s.add_task(func, 3)
s.add_task(func, 4)
s.add_task(func, 5)

# kick of the taks and start to listen to the events when tasks start or finish
s.start()
s.listen()
```

You should see following logs:

```
{'waiting': 5, 'running': 0, 'failed': 0, 'finished': 0, 'total': 5} ________ START
{'waiting': 5, 'running': 0, 'failed': 0, 'finished': 0, 'total': 5} ________ using 4 workers
{'waiting': 5, 'running': 0, 'failed': 0, 'finished': 0, 'total': 5} ________ worker 58884 started
{'waiting': 4, 'running': 1, 'failed': 0, 'finished': 0, 'total': 5} ________ task-0: started
{'waiting': 4, 'running': 1, 'failed': 0, 'finished': 0, 'total': 5} ________ worker 58885 started
{'waiting': 4, 'running': 1, 'failed': 0, 'finished': 0, 'total': 5} ________ task-0: streaming log to temp/task-0.log
{'waiting': 3, 'running': 2, 'failed': 0, 'finished': 0, 'total': 5} ________ task-1: started
...

{'waiting': 0, 'running': 0, 'failed': 0, 'finished': 5, 'total': 5} ________ task-4: finished
{'waiting': 0, 'running': 0, 'failed': 0, 'finished': 5, 'total': 5} ________ worker 58884 terminated
{'waiting': 0, 'running': 0, 'failed': 0, 'finished': 5, 'total': 5} ________ FINISHED
```


####  [Running Sessions With Proxy](examples/sessions_local.py):
```bash
python examples/sessions_remote.py
```

```python
from compas_cloud import Proxy

# define a psuedo task that will take few seconds to finish
def func(a):
    import time

    for i in range(a):
        time.sleep(1)
        print('sleeped ', i, 's')


# initiate a Sessions object through Proxy that connects to a background server
p = Proxy()
s = p.Sessions()

# add several tasks to the session using different parameters
s.add_task(func, 1)
s.add_task(func, 2)
s.add_task(func, 3)
s.add_task(func, 4)
s.add_task(func, 5)

# kick of the taks and start to listen to the events when tasks start or finish
s.start()
s.listen()
```

You should be able to see same logs from above example