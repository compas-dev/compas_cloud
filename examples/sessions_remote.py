from compas_cloud import Proxy

p = Proxy()

s = p.Sessions()

def func(a):
    import time

    for i in range(a):
        time.sleep(1)
        print('sleeped ', i, 's')

    # raise RuntimeError('error example')
    return a

# s = Sessions(log_path="temp", worker_num=4)

s.add_task(func, 5)
s.add_task(func, 2)
# s.add_task(func, 3)
# s.add_task(func, 4)
# s.add_task(func, 5)


s.start()
s.listen()
