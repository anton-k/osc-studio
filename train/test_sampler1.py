from sampler1 import *

def on(x):
    return "/home/anton/music/hip-hop/samples/Fox Samples - United By Hip Hop/SET01_Bpm85_KeyC#minor/WAV/" + x

bass = on("bass.wav")
choir = on("choir.wav")
cymbal = on("cymbal.wav")
k1 = on("kick.wav")
k2 = on("kick2.wav")
piano = on("piano.wav")
snare = on("snare.wav")
s1 = on("strings legato.wav")
s2 = on("strings legato 2.wav")
perc = on("perc.wav")
h1 = on("high hat.wav")
h2 = on("high hat 2.wav")
g1 = on("guitar.wav")
g2 = on("guitar delay fx.wav")

sams = [(bass, False), (choir, False), (cymbal, True), (k1, True), (k2, True), (piano, False), (snare, True), 
        (s1, False), (s2, False), (perc, True), (h1, True), (h2, True), (g1, False), (g2, False)]
bpm = 85

c = Sam1(7700)

def load():
    for ix, sam in enumerate(sams):
        sample, isDrum = sam
        c.load(ix, sample, 85, isDrum)
    c.set_tempo(95)

load()


