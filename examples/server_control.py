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