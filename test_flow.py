from flow import  Flow
import time
import random

port = 7700
file_name = "/home/anton/Seashore.wav"

bhop = "bhopali-pad-G.wav"
hams = "hamsadhvani-pad-E.wav"
overt = "overtone-major-pad-E.wav"
planets = "early-morning-3-planets-in-the-sky-long-E.wav"
drone = "test-drone-2-E.wav"
hi = "kirwani-pad-hi-F.wav"
low = "kirwani-pad-F.wav"

def pad(x):
    return "/home/anton/music/raga/samples/pad/" + x

class Echo():
    def __init__(self, item):
        self.item = item

    def play(self, chn, name):
        print "play  : %d, %s" % (chn, name)
        self.item.play(chn, name)

    def stop(self, chn):
        print "stop  : %d" % chn
        self.item.stop(chn)

    def resume(self, chn):
        print "resume: %d" % chn
        self.item.resume(chn)

    def set_volume(self, chn, val):
        print "volume: %d, %f" % (chn, val)
        self.item.set_volume(chn, val)

methods = ['play', 'play', 'play', 'play', 'stop', 'stop', 'resume', 'set_volume']
chnls   = range(4)
files   = map(pad, [hams, drone, overt])

def send_rnd_msg(server):
    method = random.choice(methods)
    chnl   = random.choice(chnls)

    if method is 'play':
        name   = random.choice(files)
        server.play(chnl, name)
    if method is 'stop':
        server.stop(chnl)        
    if method is 'resume':
        server.resume(chnl)
    if method is 'set_volume':
        volume = random.random()
        server.set_volume(chnl,volume) 

def main():
    c = Flow(port, 8)
    echo = Echo(c)
    while True:
        send_rnd_msg(echo)
        time.sleep(2)

if __name__=='__main__':
    main()