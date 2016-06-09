import wx, glob, os.path, argparse, unicodedata, json
from wx_utils import *
from knob import *
from toggle_matrix import *
import osc
import argparse

SIZE    = 3
WIDTH   = 453
HEIGHT  = 150

FONT_SIZE = 14

def set_fixed_size(window, w, h):
    window.SetSizeHints(w, h, w, h)

def unicode2string(x):
    return unicodedata.normalize('NFKD', x).encode('ascii','ignore')

def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def parse_args():
    parser = argparse.ArgumentParser(description="UI for flow audio server.")
    parser.add_argument('--flow', dest='flow', type=int, nargs='?', help = 'OSC port for flow')
    parser.add_argument('--sampler', dest='sampler', type=int, nargs='?', help = 'OSC port for sampler.')
    parser.add_argument('--tap', dest='tap', type=int, nargs='?', help = 'OSC port for tap.')

    args = parser.parse_args()
    return args.flow, args.sampler, args.tap

def assign_cmd_args(state):
    flow, sampler, tap = parse_args()
    
    if flow is not None:
        state.port_flow = flow

    if sampler is not None:
        state.port_sampler = sampler

    if tap is not None:
        state.port_tap = tap


class PrimClient:
    def __init__(self):
        self.client = None      

    def load(self, path):
        self.client.send("/load", path)

    def set_volume(self, volume):
        self.client.send("/set_volume", volume)

    def start(self, port, path):
        if self.client is not None:
            self.stop()
        self.client = osc.OscClient(port)  
        if path is not None:      
            self.client.send("/load", path)
            #self.client.send("/start")

    def stop(self):
        self.client.send("/stop")


class Client:
    def __init__(self):
        self.flow = PrimClient()
        self.sampler = PrimClient()
        self.tap = PrimClient()

def client_path(client_name, path):
    res = os.path.join(path, client_name)
    if os.path.isdir(res):
        return res
    else:
        return None

def flow_path(path):
    return client_path('flow', path)

def sampler_path(path):
    return client_path('sampler', path)

def tap_path(path):
    return client_path('tap', path)

class St:
    def __init__(self):
        self.client         = Client()
        self.cfg            = wx.Config("ui-osc-studio-master")
        self.names          = ['flow', 'sampler', 'tap']

        self.path           = self.cfg.Read('path', '')
        self.port_flow      = self.cfg.ReadInt('port_flow', 7700)
        self.port_sampler   = self.cfg.ReadInt('port_sampler', 7701)
        self.port_tap       = self.cfg.ReadInt('port_tap', 7702)

        self.volumes        = [0.5] * 3
        self.ons            = [True] * 3

        self.tracks         = []
        assign_cmd_args(self)


    def save(self):
        self.cfg.Write('path', self.path)
        self.cfg.WriteInt('port_flow', self.port_flow)
        self.cfg.WriteInt('port_sampler', self.port_sampler)
        self.cfg.WriteInt('port_tap', self.port_tap)

    def start_client(self):
        load_tracks(self.path)
        self.client.flow.start(self.port_flow, flow_path(self.path))
        self.client.sampler.start(self.port_sampler, sampler_path(self.path))
        self.client.tap.start(self.port_tap, tap_path(self.path))

    def stop_client(self):        
        self.client.flow.stop()
        self.client.sampler.stop()
        self.client.tap.stop()

    def close(self):     
        print "Stop client"   
        self.stop_client()
        print "Save state"
        self.save()

    def load_tracks(self, path):      
        for p, client in [(flow_path(path), self.client.flow),
                (sampler_path(path), self.client.sampler),
                (tap_path(path), self.client.tap)]:
            if p is not None:
                client.load(p)
        self.path = path

def make_dialog(dialog_constructor, window, state):
    def go(evt):
        dialog = dialog_constructor(window, state)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Close()
    return go

def init_menu(window, state):
    def on_mute(evt):
        pass   

    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Load', cbk = get_dir_dialog(lambda path: state.load_tracks(path), defaultPath = state.path)),
            normalItem('Tracks', cbk = make_dialog(PrefDialog, window, state)),            
            normalItem('Settings', cbk = make_dialog(PrefDialog, window, state)),            
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])


def setup(frame, state):

    def on_tap(x, y, is_on):
        act = None
        if x == 0:
            act = state.client.flow
        elif x == 1:
            act = state.client.sampler
        elif x == 2: 
            act = state.client.tap

        if act is not None:
            if is_on:
                act.start()
            else:
                act.stop()
        
    set_fixed_size(frame, WIDTH, HEIGHT)
    state.start_client()    
    frame.SetFont(get_font())

    volumes = hor([Knob(frame, 0.5, cbk = setter) for setter in [state.client.flow.set_volume, state.client.sampler.set_volume, state.client.tap.set_volume]])
    taps    = ToggleMatrix(frame, (SIZE, 1), names = state.names, cbk = on_tap, init_values = [True] * 3)
    layout  = ver([Cell(volumes, 3), Cell(taps, 1)])
    frame.SetSizer(layout)

    init_menu(frame, state)

    def on_close(evt):
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)


class PrefDialog(wx.Dialog):
    def __init__(self, parent, state):
        wx.Dialog.__init__(self, parent, -1)
        pnl = wx.Panel(self)    
        font = get_font()
        
        x1 = 20
        x2 = 150
        dy = 35
        t1 = wx.StaticText(pnl, label="OSC flow", pos = (x1, 20))    
        t2 = wx.StaticText(pnl, label="OSC sampler", pos = (x1, 20 + dy))   
        t3 = wx.StaticText(pnl, label="OSC tap",  pos = (x1, 20 + 2 * dy))   
        #t4 = wx.StaticText(pnl, label="Font",    pos = (x1, 20 + 3 * dy))   
        
        v1 = spin_ctrl(pnl, initial=state.port_flow, min=0, max=100000, pos = (x2, 20))
        v2 = spin_ctrl(pnl, initial=state.port_sampler, min=0, max=100000, pos = (x2, 20 + dy))
        v3 = spin_ctrl(pnl, initial=state.port_tap, min=0, max=100000, pos = (x2, 20 + 2 * dy))        
        #v4 = spin_ctrl(pnl, initial=14, min=8, max=24, pos = (x2, 20 + 3 * dy))
        self.port_flow = v1
        self.port_sampler = v2                
        self.port_tap = v3

        btn = wx.Button(pnl, label="Save", pos = (100, 20 + 3 * dy))
        pnl.Bind(wx.EVT_BUTTON, lambda evt: self.on_save(state, evt), btn)

        [t.SetFont(font) for t in [t1, t2, t3, v1, v2, v3, btn]]
        self.SetTitle("Settings")        
        self.SetSize((270, 170))

    def on_save(self, state, evt):
        def on_port(ui, cur_port, st, cur_path):
            port = ui.GetValue()
            if cur_port != port:
                cur_port = port
                st.start(port, cur_path)

        on_port(self.port_flow, state.port_flow, state.client.flow, flow_path(state.path))
        on_port(self.port_sampler, state.port_sampler, state.client.sampler, sampler_path(state.path))
        on_port(self.port_tap, state.port_tap, state.client.tap, tap_path(state.path))
        state.save()
        self.Close()
   
def main():
    runApp(setup, 'sampler', size = (WIDTH, HEIGHT), state = St())

if __name__ == '__main__':
    main()

