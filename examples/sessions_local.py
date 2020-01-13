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