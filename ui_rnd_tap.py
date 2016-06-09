from rnd_tap import *
from wx_utils import *
import wx
import unicodedata
import glob
from knob import Knob
import random
import osc
import argparse
import csnd6

from wx.lib.pubsub import Publisher

def unicode2string(x):
    return unicodedata.normalize('NFKD', x).encode('ascii','ignore')

SIZE = 32
FONT_SIZE = 14
WIDTH  = 230
HEIGHT = 100

def parse_args():
    parser = argparse.ArgumentParser(description="UI for flow audio server.")    
    parser.add_argument('--portout', dest='port_out', type=int, nargs='?', help = 'OSC output port')
    parser.add_argument('--path', dest='path', type=str, nargs='?', help = 'Path to load.')
    parser.add_argument('--csound', dest='start_csound', action='store_true', help = 'Starts csound server inside the ui program.')    
    parser.add_argument('--no-csound', dest='start_csound', action='store_false', help = 'Don\'t start csound server inside the ui program.')    
    parser.set_defaults(start_csound = True)

    return parser.parse_args()    

def assign_cmd_args(state, args):
    port_out, path, start_csound = args.port_out, args.path, args.start_csound
    
    if port_out is not None:
        state.port_out = port_out

    if path is not None:
        state.path = path

    state.start_csound_flag = start_csound

class TapArgs:
    def __init__(self, port_out = None, path = None, start_csound = True):
        self.port_out = port_out
        self.path = path
        self.start_csound = start_csound

class St:
    def __init__(self, args):
        self.cfg = wx.Config('ui-rnd-tap-config')        
        self.client = None           
        self.server = None
        self.path = self.cfg.Read('dir', '')
        self.port_out = self.cfg.ReadInt('port_out', 7700)
        self.volume = self.cfg.ReadFloat('volume', 0.5)

        assign_cmd_args(self, args)
        self.load_csound_server(self.port_out)

        print "Load state"
        print  "dir: %s" % self.path
        print  "out: %d" % self.port_out
        print  "vol: %f" % self.volume

    def save(self):
        self.cfg.Write('dir', self.path)
        self.cfg.WriteInt('port_out', self.port_out)
        self.cfg.WriteFloat('volume', self.volume)

    def start_csound(self):
        if self.start_csound_flag:
            c = self.engine
            c.SetOption("--omacro:PORT=%d" % self.port_out)
            c.Compile('rnd_tap_space.csd')
            c.Start()
            perfThread = csnd6.CsoundPerformanceThread(c)
            perfThread.Play()
            self.perfThread = perfThread

    def stop_csound(self):
        if self.start_csound_flag:
            self.perfThread.Stop()
            self.perfThread.Join()
            self.engine.Reset()

    def load_csound_server(self, port):
        c = csnd6.Csound()        
        self.engine = c

    def stop_client(self):
        if self.client is not None:             
            print "Stop client"
            self.client.stop()      
            self.stop_csound()          

    def start_client(self):
        if self.client is not None:                    
            self.client.stop() 
        self.start_csound()                
        print "Start client %d" % self.port_out
        self.client = RndTap(self.port_out)
        load_samples(self, self.path)

    def close(self):        
        self.stop_client()
        print "Save state"
        self.save()

def on_tap(state, evt):
    state.client.play()

def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def on_volume(state, x):
    state.client.set_volume(2 * x)
    state.volume = x

def load_samples(state, path, wait_time = 0.02):
    state.path = path    
    if state.client is not None:
        wavs = glob.glob(path + "/*.wav")
        mp3s = glob.glob(path + "/*.mp3")
        files = map(unicode2string, wavs + mp3s)
        random.shuffle(files)
        state.client.load_list(files, wait_time)


def init_menu(frame, state):

    def on_settings(evt):
        dialog = PrefDialog(frame, state)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Close()

    def on_close(evt):        
        frame.Close()

    def on_mute(evt):
        state.client.stop()

    make_menu_bar(frame, [
        menuItem('&File', [
            normalItem('Load', cbk = get_dir_dialog(lambda path: load_samples(state, path), defaultPath = state.path)),
            normalItem('Settings', cbk = on_settings),
            normalItem('Mute', cbk = on_mute),
            normalItem('Quit', cbk = on_close)
        ])            
    ])


def setup(frame, state):
    state.start_client()        
    frame.SetSizeHints(WIDTH, HEIGHT, WIDTH, HEIGHT)        
    btn = button(frame, 'Play', cbk = lambda evt: on_tap(state, evt))
    btn.SetFont(get_font())   
    init_menu(frame, state) 

    def on_close(evt):        
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)

class TapFrame(wx.Frame):
    def __init__(self, args, parent = None, id = -1, title = "Tap", size = (WIDTH, HEIGHT)):
        state = St(args)
        wx.Frame.__init__(self, parent, id, title, size)
        setup(self, state)
        self.state = state
        self.Centre()
        self.Show(True)

        Publisher().subscribe(self.on_load, "tap_load")
        Publisher().subscribe(self.on_stop, "tap_stop")
        Publisher().subscribe(self.on_volume, "tap_volume")

    def on_load(self, msg):        
        path = msg.data[0] 
        load_samples(self.state, path)            

    def on_stop(self, msg):
        self.state.client.stop()            

    def on_volume(self, msg):
        volume = msg.data
        self.state.client.set_volume(volume)          

class PrefDialog(wx.Dialog):
    def __init__(self, parent, state):
        wx.Dialog.__init__(self, parent, -1)

        pnl = wx.Panel(self)    
        font = get_font()
        
        x1 = 20
        x2 = 150
        dy = 35
        t1 = wx.StaticText(pnl, label="OSC out", pos = (x1, 20))    
        t2 = wx.StaticText(pnl, label="OSC in",  pos = (x1, 20 + dy))   
        t3 = wx.StaticText(pnl, label="Volume",  pos = (x1, 20 + 2 * dy))          
        
        v1 = spin_ctrl(pnl, initial=state.port_out, min=0, max=100000, pos = (x2, 20))
        v3 = hor_slider(pnl, initial = state.volume, pos = (x2, 20 + 2 * dy), size = (100, -1), cbk = lambda x: on_volume(state, x))        
        self.port_out = v1

        btn = wx.Button(pnl, label="Save", pos = (100, 20 + 3 * dy))
        pnl.Bind(wx.EVT_BUTTON, lambda evt: self.on_save(state, evt), btn)

        [t.SetFont(font) for t in [t1, t2, t3, v1, v3, btn]]
        self.SetTitle("Settings")        
        self.SetSize((270, 170))

    def on_save(self, state, evt):
        port_out = self.port_out.GetValue()
        if (state.port_out != port_out):
            state.port_out = port_out
            state.start_client()
        state.save()
        self.Close()

def main():
    runApp(setup, 'random', size = (WIDTH, HEIGHT), state = St(parse_args()))

if __name__ == '__main__':
    main()
