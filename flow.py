import OSC

port = 7700
 

def msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

class Flow():
    def __init__(self, port, size = 16):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))
        self.size = size

    def play(self, channel, file_name):
        self.client.send(msg("/play", channel, file_name))

    def play_once(self, channel, file_name):
        self.client.send(msg("/play_once", channel, file_name))

    def play_period(self, channel, file_name, period):
        self.client.send(msg("/play_period", channel, file_name, period))

    def stop(self, channel):
        self.client.send(msg("/stop", channel))

    def resume(self, channel):       
        self.client.send(msg("/resume", channel))

    def set_volume(self, channel, volume):
        self.client.send(msg("/set_volume", channel, volume))

    def set_gain(self, channel, gain):
        self.client.send(msg("/set_gain", channel, gain))

    def set_master_volume(self, volume):
        self.client.send(msg("/set_master_volume", volume))

    def set_master_gain(self, gain):
        self.client.send(msg("/set_master_gain", gain))

    def set_fade(self, fade):
        self.client.send(msg("/set_fade", fade))

    def mute(self):
        for i in range(self.size):
            self.set_volume(i, 0)

    def stop_all(self):
        for i in range(self.size):
            self.stop(i)

    def resume_all(self):
        for i in range(self.size):
            self.resume(i)

    def set_volume_all(self, volume):
        for i in range(self.size):
            self.set_volume_all(i, volume)

