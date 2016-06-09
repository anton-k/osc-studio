import wx
from wx_utils import *
from flow import *
from knob import *
from toggle_matrix import *
import os.path, glob, unicodedata, argparse, json, time
import osc
import csnd6

from wx.lib.pubsub import Publisher

SIZE    = 4
WIDTH   = 453
HEIGHT  = 150

PLAY_LOOP = 'loop'
PLAY_ONCE = 'once'
PLAY_PERIOD = 'period'

FONT_SIZE = 14

def play_by_type(client, channel, file_name, play_type, period):
    print  "play %d  %s %s %f" % (channel, file_name, play_type, period)
    if play_type == PLAY_LOOP:
        print 1
        client.play(channel, file_name)
    elif play_type == PLAY_ONCE:
        print 2
        client.play_once(channel, file_name)
    elif play_type == PLAY_PERIOD:
        print 3
        print "play period"
        client.play_period(channel, file_name, period)


def unicode2string(x):
    return unicodedata.normalize('NFKD', x).encode('ascii','ignore')

def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def set_fixed_size(window, w, h):
    window.SetSizeHints(w, h, w, h)

EVT_RESULT_ID = wx.NewId()
 
def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)
 
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

def parse_args():
    parser = argparse.ArgumentParser(description="UI for flow audio server.")
    parser.add_argument('--portout', dest='port_out', type=int, nargs='?', help = 'OSC output port')
    parser.add_argument('--path', dest='path', type=str, nargs='?', help = 'Path to load.')
    parser.add_argument('--csound', dest='start_csound', action='store_true', help = 'Starts csound server inside the ui program.')    
    parser.add_argument('--no-csound', dest='start_csound', action='store_false', help = 'Don\'t start csound server inside the ui program.')    
    parser.set_defaults(start_csound = True)

    args = parser.parse_args()
    return args

def assign_cmd_args(state, args):
    port_out, path, start_csound = args.port_out, args.path, args.start_csound
    
    if port_out is not None:
        state.port_out = port_out

    if path is not None:
        state.path = path

    state.start_csound_flag = start_csound


class FlowArgs:
    def __init__(self, port_out = None, path = None, start_csound = True):
        self.port_out = port_out
        self.path = path
        self.start_csound = start_csound   

class St:
    def __init__(self, args):
        self.client = None
        self.server = None
        self.cfg = wx.Config('ui-flow')  
      
        self.names      = []
        self.files      = []
        self.path       = self.cfg.Read('path', '')
        self.size       = 4
        self.port_out   = self.cfg.ReadInt('port_out', 7700) 
        self.master_volume = self.cfg.ReadFloat('master_volume', 0.5)

        assign_cmd_args(self, args)

        self.load_csound_server(self.port_out)

        print "Load state"
        print "path %s" % self.path
        print "size %d" % self.size
        print "port_out %d" % self.port_out
        print "master_volume %f" % self.master_volume

    def save(self):
        self.cfg.Write('path', self.path)        
        self.cfg.WriteInt('port_out', self.port_out)
        self.cfg.WriteFloat('master_volume', self.master_volume)

    def close(self):     
        print "Stop client"   
        self.stop_client()
        print "Save state"
        self.save()

    def start_csound(self):
        if self.start_csound_flag:
            c = self.engine
            c.SetOption("--omacro:PORT=%d" % self.port_out)
            c.Compile('flow.csd')
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

    def start_client(self):
        if self.client is not None:                    
            self.client.stop_all() 
        self.start_csound()                
        print "Start client %d" % self.port_out
        self.client = Flow(self.port_out)
        load_samples(self, self.path)

    def stop_client(self):
        if self.client is not None:            
            self.client.stop_all()
            self.stop_csound()


def read_item_desc(item):
    name = item.get('name', '')
    file = item.get('file', None)
    volume = item.get('volume', 0.5)
    is_on = item.get('on', True)
    gain = item.get('gain', 1)
    play_type = item.get('type', PLAY_LOOP)
    play_period_time = item.get('period', 1)
    return name, file, volume, is_on, gain, play_type, play_period_time

def load_samples(state, path, wait_time = 0.001):    
    def wait():
        time.sleep(wait_time)

    if state.client is None or len(path) == 0:
        print "Nothing to load"
        return None  

    names = []
    files = []
    ons   = []
    volumes = [] 
    gains = []  
    master_volume = 0.5
    master_gain = 1
    play_types = []
    play_periods = []
    
    index_file = os.path.join(path, "index.json")
    if os.path.isfile(index_file):
        # try:
        with open(index_file, "r") as myfile:
            desc = json.load(myfile) 
        if type(desc) is list:
            items = desc            
        else:
            items = desc['tracks'] 
            master_volume = desc.get('volume', master_volume)
            master_gain = desc.get('gain', master_gain)

        for item in items:
            name, file, volume, is_on, gain, play_type, play_period = read_item_desc(item)
            abs_file = os.path.join(path, file)
            files.append(abs_file)
            names.append(name)
            volumes.append(volume)
            gains.append(gain)
            ons.append(is_on)
            play_types.append(play_type)
            play_periods.append(play_period)
        # except:
        #     print "Failed to load index.json"
    else:                
        wavs = glob.glob(os.path.join(path, "*.wav"))
        mp3s = glob.glob(os.path.join(path, "*.mp3"))
        files = map(unicode2string, wavs + mp3s)        
        names = map(lambda x: os.path.splitext(os.path.basename(x))[0][0:6], files)
        ons   = len(files) * [True]
        volumes = len(files) * [0.5]   
        gains = len(files) * [1] 
        play_types = len(files) * [PLAY_LOOP]
        play_periods = len(files) * [1]

    size = len(files)

    if size == 0:
        print "Failed to load %s." % path
        return None

    print "size %d" % size
    print str(play_types)
    print str(play_periods)
    for ix in range(size):
        state.client.set_gain(ix, gains[ix])
        state.client.set_volume(ix, volumes[ix]) 
        wait()       
        is_on = ons[ix]
        if is_on:
            play_by_type(state.client, ix, files[ix], play_types[ix], play_periods[ix])            
        else:
            state.client.stop(ix)
        wait()

    for ix in range(len(state.files) - size):
        state.client.stop(size + ix)
        wait()

    print "Load"
    print names    
    print files
    print ons
    print volumes

    time.sleep(1.25)
    state.client.set_master_gain(master_gain)
    state.client.set_master_volume(master_volume)
    

    state.path = path
    state.names = names
    state.files = files
    state.ons   = ons
    state.volumes = volumes
    state.master_volume = master_volume
    state.master_gain = master_gain
    state.gains = gains
    state.play_types = play_types
    state.play_periods = play_periods

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

    def on_load(path):
        print state.path
        load_samples(state, path)        
        update_ui(window, state)

    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Load', cbk = get_dir_dialog(on_load, defaultPath = state.path)),
            normalItem('Settings', cbk = make_dialog(PrefDialog, window, state)),
            normalItem('Mute', cbk = on_mute),
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])

def init_osc(frame, state):
    state.start_client()

def setup(frame, state):
    init_osc(frame, state)
    init_ui(frame, state)
    update_ui(frame, state)
    
    def on_close(evt):
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)
    frame.Bind(wx.EVT_PAINT, lambda evt: init_ui(frame, state))

def init_ui(frame, state):
    pnl = wx.Panel(frame)
    frame.pnl = pnl
    frame.volumes_sizer = hor([])
    frame.taps_sizer = hor([])

    frame.volumes = None
    frame.taps = None
    frame.layout  = ver([Cell(frame.volumes_sizer, 3), Cell(frame.taps_sizer, 1)])
    frame.size = 0
    pnl.SetSizer(frame.layout)
    pnl.SetFont(get_font())     

def update_ui(frame, state):
    pnl = frame.pnl
    size = len(state.files)
    if frame.size == size:
        if frame.taps is not None:
            frame.taps.set_names(state.names)
            frame.taps.set_values(state.ons)            
        if frame.volumes is not None:
            for ix, knob in enumerate(frame.volumes):
                knob.set_value(state.volumes[ix])
        return None

    frame.size = size    
    def on_tap(x, y, is_on):
        if is_on:
            play_by_type(state.client, x, state.files[x], state.play_types[x], state.play_periods[x])            
        else:
            state.client.stop(x)

    def on_volume(channel):    
        def go(volume):
            state.client.set_volume(channel, volume)
        return go    
    
    w = int(size * float(WIDTH) / 4)
    h = HEIGHT
    set_fixed_size(frame, w, h)
    
    frame.volumes = [Knob(pnl, state.volumes[i], cbk = on_volume(i)) for i in range(size)]
    reset_sizer(frame.volumes_sizer, frame.volumes)
    frame.taps    = ToggleMatrix(pnl, (size, 1), names = state.names, cbk = on_tap, init_values = state.ons)
    reset_sizer(frame.taps_sizer, [frame.taps])

    init_menu(frame, state)

def on_volume(state, x):
    state.client.set_master_volume(2 * x)
    state.master_volume = x

class FlowFrame(wx.Frame):
    def __init__(self, args, parent = None, id = -1, title = "Flow", size = (WIDTH, HEIGHT)):
        state = St(args)
        wx.Frame.__init__(self, parent, id, title, size)
        setup(self, state)
        self.state = state
        self.Centre()
        self.Show(True)

        Publisher().subscribe(self.on_load, "flow_load")
        Publisher().subscribe(self.on_stop, "flow_stop")
        Publisher().subscribe(self.on_volume, "flow_volume")

    def on_load(self, msg):
        path = msg.data[0]        
        load_samples(self.state, path)
        update_ui(self, self.state)

    def on_stop(self, msg):
        self.state.client.stop_all()
        self.taps.set_values([False] * self.state.size)

    def on_volume(self, msg):
        volume = msg.data
        self.state.client.set_master_volume(volume)


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
        #t4 = wx.StaticText(pnl, label="Font",    pos = (x1, 20 + 3 * dy))   
        
        v1 = spin_ctrl(pnl, initial=state.port_out, min=0, max=100000, pos = (x2, 20))
        v3 = hor_slider(pnl, initial = state.master_volume, pos = (x2, 20 + 2 * dy), size = (100, -1), cbk = lambda x: on_volume(state, x))
        #v4 = spin_ctrl(pnl, initial=14, min=8, max=24, pos = (x2, 20 + 3 * dy))
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
    state = St(parse_args())
    runApp(setup, 'flow', state = state)

if __name__ == '__main__':
    main()
