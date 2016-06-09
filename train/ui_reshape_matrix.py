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
        self.set_size(4, 3)

    def set_size(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self.names = map(str, range(self.size_x * self.size_y, 0, -1))
        self.ons = [False] * (self.size_x * self.size_y)

    def close(self):
        pass


def init_menu(window, state):
    def on_size(m, n):
        def go(evt):
            if state.size_x == m and state.size_y == n:
                return None
            state.set_size(m, n)                
            update_ui(window, state)            
        return go

    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Set 1 1', cbk = on_size(1, 1)),
            normalItem('Set 3 2', cbk = on_size(3, 2)),
            normalItem('Set 4 4', cbk = on_size(4, 4)),
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])

def init_ui(frame, state):
    pnl = wx.Panel(frame)
    frame.pnl = pnl   
    pnl.SetFont(get_font()) 
    frame.taps = None      

def update_ui(frame, state):
    init_menu(frame, state)

    def on_tap(x, y, is_on):
        print "tap"

    def on_volume(channel):    
        def go(volume):
            print "set_volume %f" % volume
        return go

    size_x = state.size_x
    size_y = state.size_y
    pnl = frame.pnl

    print (size_x, size_y)
    w = int(size_x * float(WIDTH) / 4)
    h = int(size_y * float(HEIGHT) / 3)
    print w, h
    set_fixed_size(frame, w, h) 

   # if frame.taps is not None:
   #     frame.taps.Destroy()
    frame.taps = ToggleMatrix(pnl, (size_x, size_y), names = state.names, cbk = on_tap, init_values = state.ons, widget_size = (w, h - 20))    
    init_key_press(frame, state)
  
key_rows = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '\\'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']]

key_to_coord = {}

for i, row in enumerate(key_rows):
    for j, val in enumerate(row):
        print val, ord(val), i, j
        key_to_coord[ord(val)] = (j, i)

def get_key_coord(keycode):
    return key_to_coord.get(keycode, None)

def init_key_press(frame, state):
    def on_press(evt):        
        keycode = evt.GetRawKeyCode()        
        coord = get_key_coord(keycode)
        if coord is not None:
            x, y = coord
            if x < state.size_x and y < state.size_y:
                frame.taps.toggle(x, y)
        print keycode, coord

    print "Press bind"
    frame.taps.Bind(wx.EVT_KEY_DOWN, on_press)
    frame.taps.SetFocus()

def init_close(frame, state):
    
    def on_close(evt):
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)
    

def setup(frame, state):
    init_ui(frame, state)
    update_ui(frame, state)
    init_close(frame, state)


def main():
    runApp(setup, 'flow', state = St())

if __name__ == '__main__':
    main()

