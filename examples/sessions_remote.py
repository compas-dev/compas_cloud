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
