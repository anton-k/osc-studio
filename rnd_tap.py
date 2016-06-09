import OSC
import time

def msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

def vectorize(f, arg):
    if type(arg) is list:
        for x in arg:
            f(x)
    else:
        f(arg)

class RndTap():
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))        

    def load(self, index, file_name):        
        self.client.send(msg("/load", index, file_name))

    def load_list(self, files, wait_time = 0):
        self.set_size(len(files))
        for ix, f in enumerate(files):
            self.load(ix, f)
            time.sleep(wait_time)

    def play(self):
        self.client.send(msg("/play", 0))

    def play_at(self, pan, dist):
        self.client.send(msg("/play_at", pan, dist))

    def stop(self):
        self.client.send(msg("/stop", 0))

    def clear(self):
        self.client.send(msg("/clear", 0))

    def set_volume(self, volume):
        self.client.send(msg("/set_volume", volume))

    def set_volume(self, gain):
        self.client.send(msg("/set_gain", gain))

    def set_size(self, size):
        self.client.send(msg("/set_size", size))
