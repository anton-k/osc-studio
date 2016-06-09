from rnd_tap import RndTap, RndList

def on(x):
    return "/home/anton/music/raga/samples/fx/revolution/" + x

files = map(on, [
    "castro-11.wav",
    "castro-22.wav",
    "castro-33.wav",
    "Ghandi-11.wav",
    "Ghandi-22.wav",
    "Ghandi-33.wav" ])

#c = RndTap(port = 7700, size = len(files))
#c.load(files)

q = RndList(port = 7700, files = files)