from flow import Flow
import os.path

def sf(x):
    return os.path.join("/home/anton/music/raga/samples/sakura-fx", x)

tq = sf("TQT29.wav")
rattle = sf("fan_rattle_1.wav")
pc = sf("computer_mania1.wav")
piano = sf("passage1.wav")
viola = sf("viola harmonic gliss G.wav")

q = Flow(7700)