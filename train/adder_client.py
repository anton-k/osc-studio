import OSC

def msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

class Add():
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))

    def printer(self, n):
        self.client.send(msg("/echo", n))

    def add(self, n):
        self.client.send(msg("/add", n))

    def show(self):
        self.client.send(msg("/show", 0))

    def quit(self):
        self.client.send(msg("/quit", 0))


