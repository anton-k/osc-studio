import wx
from wx_utils import *
from sampler import *
from knob import *
from toggle_matrix import *

PORT    = 7700
SIZE    = 4
WIDTH   = 453
HEIGHT  = 150

FONT_SIZE = 14

def load_samples(path):
    pass

def set_fixed_size(window, w, h):
    window.SetSizeHints(w, h, w, h)

def init_menu(window, st):
    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Load', cbk = get_dir_dialog(load_samples)),
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])

def on_volume(channel):    
    def go(volume):
        pass

    return go

def on_tap(x, y, is_on):
    if is_on:
        client.resume(x)
    else:
        client.stop(x)

def printer(name):
    def go(value):
        print name + ": "  + str(value)
    return go

def setup(frame):
    set_fixed_size(frame, WIDTH, HEIGHT)    
    q1 = spin_ctrl(frame, 3, 0, 20, printer("spin"))
    q2 = hor_slider(frame, 3, 0, 20, printer("slider"))
    layout = hor([Cell(q1, 0), Cell(q1, 1)])
    frame.SetSizer(layout)
    init_menu(frame, None)

def main():
    runApp(setup, 'test')

if __name__ == '__main__':
    main()
