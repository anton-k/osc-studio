import OSC

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

class Sam():
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))

    def load(self, ix,  file_name, bpm, is_drum = False):
        self.client.send(msg("/load", ix, file_name, bpm, 1 if is_drum else 0))

    def play(self, channel, ix):
        self.client.send(msg("/play", channel, ix))

    def play_once(self, channel, ix):
        self.client.send(msg("/play_once", channel, ix))

    def play_period(self, channel, ix, period):
        self.client.send(msg("/play_period", channel, ix, period))

    def stop(self, channel):
        vectorize(lambda x: self.client.send(msg("/stop", x)), channel)

    def resume(self, channel):
        vectorize(lambda x: self.client.send(msg("/resume", x)), channel)

    def delete(self, index):
        vectorize(lambda x: self.client.send(msg("/delete", x)), index)

    def set_volume(self, channel, volume):
        vectorize(lambda x: self.client.send(msg("/set_volume", x, volume)), channel)

    def set_master_volume(self, volume):
        self.client.send(msg("/set_master_volume", volume))

    def set_gain(self, channel, gain):
        vectorize(lambda x: self.client.send(msg("/set_gain", x, gain)), channel)

    def set_master_gain(self, gain):
        self.client.send(msg("/set_master_gain", gain))

    def set_speed(self, channel, speed):
        vectorize(lambda x: self.client.send(msg("/set_speed", x, speed)), channel)

    def set_tempo(self, tempo):
        self.client.send(msg("/set_tempo", tempo))

    def fade_out_and_stop_all(self, duration):
        self.client.send(msg("/fade_out_and_stop_all", duration))



