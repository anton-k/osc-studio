import OSC

port = 7700

def msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

class Sam1():
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))

    def load(self, ix,  file_name, bpm, isDrum = False):
        self.client.send(msg("/load", ix, file_name, bpm, 1 if isDrum else 0))

    def play(self, ix):
        self.client.send(msg("/play", ix))

    def stop(self):
        self.client.send(msg("/stop", 0))

    def resume(self):
        self.client.send(msg("/resume", 0))

    def set_volume(self, volume):
        self.client.send(msg("/set_volume", volume))

    def set_speed(self, speed):
        self.client.send(msg("/set_speed", speed))

    def set_tempo(self, tempo):
        self.client.send(msg("/set_tempo", tempo))
