import osc
import OSC

def msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

class Flow():
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))

    def load(self, n):
        self.client.send(msg("/load", n))

    def play(self):
        self.client.send(msg("/play"))

    def set_volume(self, ix, n):
        self.client.send(msg("/set_volume", ix, n))

    def quit(self):
        self.client.send(msg("/quit"))

