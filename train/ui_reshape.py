import wx
from wx_utils import *
from knob import *
from toggle_matrix import *


WIDTH   = 453
HEIGHT  = 150

FONT_SIZE = 14


def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def set_fixed_size(window, w, h):
    window.SetSizeHints(w, h, w, h)

class St():
    def __init__(self):
        self.set_size(4)

    def set_size(self, size):
        self.size = size
        self.names = map(str, range(self.size, 0, -1))
        self.ons = [False] * self.size

    def close(self):
        pass


def init_menu(window, state):
    def on_size(n):
        def go(evt):
            if state.size != n:
                state.set_size(n)                
                update_ui(window, state)            
        return go

    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Set 1', cbk = on_size(1)),
            normalItem('Set 2', cbk = on_size(2)),
            normalItem('Set 4', cbk = on_size(4)),
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])

def init_ui(frame, state):
    pnl = wx.Panel(frame)
    frame.pnl = pnl
    frame.volumes = hor([])
    frame.taps    = hor([])
    frame.layout  = ver([Cell(frame.volumes, 3), Cell(frame.taps, 1)])
    pnl.SetSizer(frame.layout)
    pnl.SetFont(get_font())    

    update_ui(frame, state)

def clear_ui(frame, state):
    pass

def update_ui(frame, state):
    def on_tap(x, y, is_on):
        print "tap"

    def on_volume(channel):    
        def go(volume):
            print "set_volume %f" % volume
        return go

    size = state.size
    pnl = frame.pnl

    print size
    w = int(size * float(WIDTH) / 4)
    h = HEIGHT
    set_fixed_size(frame, w, h) 

    reset_sizer(frame.volumes, [Knob(pnl, 0.5, cbk = on_volume(i)) for i in range(size)])

    taps = ToggleMatrix(pnl, (size, 1), names = state.names, cbk = on_tap, init_values = state.ons)
    reset_sizer(frame.taps, [taps])        
    init_menu(frame, state)



def init_close(frame, state):
    
    def on_close(evt):
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)
    frame.Bind(wx.EVT_PAINT, lambda evt: init_ui(frame, state))

def setup(frame, state):
    init_ui(frame, state)
    init_close(frame, state)


def main():
    runApp(setup, 'flow', state = St())

if __name__ == '__main__':
    main()

