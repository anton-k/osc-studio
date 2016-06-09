import ast
import wx
from wx_utils import *
from sampler import *
from knob import *
from toggle_matrix import *
from sampler import Sam
import osc
import glob, unicodedata, os.path, json
from knob import *
import time
import argparse
import csnd6

from wx.lib.pubsub import Publisher

SIZE    = 4
WIDTH   = 483
HEIGHT  = 200

PLAY_LOOP = 'loop'
PLAY_ONCE = 'once'
PLAY_PERIOD = 'period'

FONT_SIZE = 14

def init_if_empty(x, size, value):
    if len(x) == 0: 
        return [value] * size
    else:
        return x

def unicode2string(x):
    return unicodedata.normalize('NFKD', x).encode('ascii','ignore')

def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def current_milli_time():
    return int(round(time.time() * 1000))

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

def play_by_type(client, channel, file_index, play_type, period):
    print  "play %d  %s %s %f" % (channel, file_index, play_type, period)
    if play_type == PLAY_LOOP:
        print 1
        client.play(channel, file_index)
    elif play_type == PLAY_ONCE:
        print 2
        client.play_once(channel, file_index)
    elif play_type == PLAY_PERIOD:
        print 3
        print "play period"
        client.play_period(channel, file_index, period)


class SamplerArgs:
    def __init__(self, port_out = None, path = None, start_csound = True):
        self.port_out = port_out
        self.path = path
        self.start_csound = start_csound

class St:
    def __init__(self, args):
        self.client = None
        self.server = None
        self.cfg = wx.Config('ui-sampler')        

        self.path       = self.cfg.Read('path', '')        
        self.size_x     = self.cfg.ReadInt('size_x', 4)
        self.size_y     = self.cfg.ReadInt('size_y', 2)
        self.size       = self.size_x * self.size_y                
        self.port_out   = self.cfg.ReadInt('port_out', 7700)        
        self.volumes    = ast.literal_eval(self.cfg.Read('volumes', repr(self.size * [0])))
        self.bpms       = ast.literal_eval(self.cfg.Read('bpms', repr(self.size * [120])))
        self.tempo      = self.cfg.ReadInt('tempo', 120)       
        self.master_volume = self.cfg.ReadFloat('master_volume', 0.5)

        self.ons = init_if_empty([], self.size, False)
        self.speeds = init_if_empty([], self.size, 1)
        self.volumes = init_if_empty(self.volumes, self.size, 0.5)
        self.bpms = init_if_empty(self.bpms, self.size, 120)
        self.names = []  

        self.start_csound_flag = True

        dt = current_milli_time()
        self.double_press_time = init_if_empty([], self.size, dt)

        assign_cmd_args(self, args)

        self.load_csound_server(self.port_out)

        print "Load state"
        print "path %s" % self.path
        print "size %d %d" % (self.size_x, self.size_y)
        print "port_out %d" % self.port_out
        print "ons  %s" % repr(self.ons)
        print "vols %s" % repr(self.volumes)
        print "bpms %s" % repr(self.bpms)
        print "tempo %d" % self.tempo
        print "master %d" % self.master_volume

    def load_csound_server(self, port):
        c = csnd6.Csound()        
        self.engine = c

    def save(self):
        self.cfg.Write('path', self.path)        
        self.cfg.WriteInt('size_x', self.size_x)
        self.cfg.WriteInt('size_y', self.size_y)
        self.cfg.WriteInt('port_out', self.port_out)        
        self.cfg.Write('volumes', repr(self.volumes))
        self.cfg.Write('bpms', repr(self.bpms))
        self.cfg.WriteInt('tempo', self.tempo)
        self.cfg.WriteFloat('master_volume', self.master_volume)

    def start_csound(self):
        if self.start_csound_flag:
            c = self.engine
            c.SetOption("--omacro:PORT=%d" % self.port_out)
            c.Compile('sampler.csd')
            c.Start()
            perfThread = csnd6.CsoundPerformanceThread(c)
            perfThread.Play()
            self.perfThread = perfThread

    def stop_csound(self):
        if self.start_csound_flag:
            self.perfThread.Stop()
            self.perfThread.Join()
            self.engine.Reset()

    def start_client(self, frame):        
        if self.client is not None:                    
            self.client.stop()                 
        self.start_csound()
        print "Start client %d" % self.port_out
        self.client = Sam(self.port_out)
        self.client.set_tempo(self.tempo)
        load_samples(self, self.path)
        update_ui(frame, self)

        # for ix in range(self.size):
        #     self.client.set_volume(ix, self.volumes[ix])

        # for ix, is_on in enumerate(self.ons):
        #     if is_on:
        #         self.client.play(ix, ix)

    def stop_client(self):
        if self.client is not None:  
            self.client.fade_out_and_stop_all(0.2)          
            self.stop_csound()
            # for ix, is_on in enumerate(self.ons):
            #     for ix in range(self.size_x * self.size_y):
            #         self.client.stop(ix)

    def close(self):     
        print "Stop client"   
        self.stop_client()
        print "Save state"
        self.save()

    def set_tempo(self, x):
        if self.client is not None:
            self.client.set_tempo(x)
            self.tempo = x

    def set_master_volume(self, x):
        if self.client is not None:
            self.client.set_master_volume(2 * x)
            self.master_volume = x

    def toggle_speed(self, index):
        dt2 = current_milli_time()
        dt1 = self.double_press_time[index]        
        if (dt2 - dt1 < 230):
            self.reset_speed(index)
        else:
            self.double_press_time[index] = dt2
            self.mul_speed(index, -1)

    def boost_speed(self, index):
        print "boost speed"
        self.mul_speed(index, 2)

    def slow_speed(self, index):
        print "slow speed"
        self.mul_speed(index, 0.5)

    def mul_speed(self, index, coeff):
        self.speeds[index] = coeff * self.speeds[index]
        self.client.set_speed(index, self.speeds[index])

    def reset_speed(self, index):
        self.speeds[index] = 1
        self.client.set_speed(index, 1)

def parse_bpm(file_name):
    return 120

def parse_bpm_with_default(file_name):
    res = parse_bpm(file_name)
    if res is None:
        res = 120
    return res

def read_item_desc(item):    
    name = item.get('name','')
    file = item.get('file',None)
    bpm  = item.get('bpm', 120)
    is_drum = item.get('drum', False)
    volume = item.get('volume', 0.5)
    speed = item.get('speed', 1)
    on = item.get('on', False)    
    gain = item.get('gain', 1)
    play_type = item.get('type', PLAY_LOOP)
    play_period_time = item.get('period', 1)
    return name, file, bpm, is_drum, volume, speed, on, gain, play_type, play_period_time


def load_samples(state, path, wait_time = 0.001):    
    def wait():
        time.sleep(wait_time)

    if state.client is None or len(path) <= 0:
        print "Nothing to load"
        return None
    
    print path
    names = []
    files = []
    bpms  = []
    drums = []
    volumes = []
    gains = []
    speeds = []
    ons = []
    master_volume = 0.5
    master_gain = 1  
    play_types = []
    play_periods = []      

    index_file = os.path.join(path, "index.json")
    if os.path.isfile(index_file):
        with open(index_file, "r") as myfile:
            desc = json.load(myfile) 
        if type(desc) is list:
            items = desc
            bpm   = 120
        else:
            items = desc['tracks']
            main_bpm   = desc.get('bpm', 120)            
            master_volume = desc.get('volume', master_volume)
            master_gain = desc.get('gain', master_gain)

        for item in items:
            name, file, bpm, is_drum, volume, speed, is_on, gain, play_type, play_period_time = read_item_desc(item)
            if file is None:
                print "Nothing to load"
                return None
            abs_file = os.path.join(path, file)
            names.append(name)
            files.append(abs_file)
            bpms.append(bpm)
            drums.append(is_drum)
            volumes.append(volume)
            gains.append(gain)
            speeds.append(speed)
            ons.append(is_on)
            play_types.append(play_type)
            play_periods.append(play_period_time)

        size = len(files)
    else:
        wavs = glob.glob(os.path.join(path, "*.wav"))
        mp3s = glob.glob(os.path.join(path, "*.mp3"))
        files = map(unicode2string, wavs + mp3s)
        size = len(files)
        names = [''] * size
        bpms  = [120] * size
        drums = [False] * size
        volumes = [0.5] * size        
        speeds = [1] * size
        ons = [False] * size
        gains = [1] * size
        play_types = [PLAY_LOOP] * size
        play_periods = [1] * size


    if size == 0:
        print "Failed to load %s." % path
        return None

    size_x, size_y = get_matrix_sizes(size)

    state.client.fade_out_and_stop_all(0.2)
    time.sleep(0.25)

    #for ix in range(state.size):
    #    state.client.delete(ix)


    state.client.set_master_gain(master_gain)
    state.client.set_master_volume(master_volume)
    wait()

    print "tempo is %d" % main_bpm
    state.client.set_tempo(main_bpm)
    wait()

    for ix in range(size):
        print "set_gain %d %f" % (ix, gains[ix])
        state.client.set_gain(ix, gains[ix])
        print "set_volume %d %f" % (ix, volumes[ix])
        state.client.set_volume(ix, volumes[ix])
        wait()
        print "set_speed %d %f" % (ix, speeds[ix])        
        state.client.set_speed(ix, speeds[ix])
        wait()
        print "load %d %s %d" % (ix, files[ix], bpms[ix])
        state.client.load(ix, files[ix], bpms[ix], drums[ix])
        wait()
        if ons[ix]:
            state.client.play[ix]
            wait()

    state.path = path
    state.bpm = main_bpm
    state.names = names
    state.volumes = volumes
    state.speeds = speeds
    state.ons = ons
    state.size = size
    state.size_x = size_x
    state.size_y = size_y
    
    state.master_volume = master_volume
    state.master_gain = master_gain

    state.play_types = play_types
    state.play_periods = play_periods

    dt = current_milli_time()
    state.double_press_time = init_if_empty([], state.size, dt)

def get_matrix_sizes(n):
    if n < 7:
        return (n, 1)
    if n < 17:
        if n % 2 == 0:
            return (n / 2, 2)
        else:
            return ((n+1)/2, 2)
    if n < 25:
        if n % 3 == 0:
            return ( n / 3, 3 )
        elif (n + 1) % 3 == 0:
            return ( (n + 1) / 3, 3 )
        else: 
            return ( (n + 2) / 3, 3 )

    if n < 33:
        if n % 4 == 0:
            return ( n / 4, 4 )
        elif (n + 1) % 4 == 0:
            return ( (n + 1) / 4, 4 )
        elif (n + 2) % 4 == 0:
            return ( (n + 2) / 4, 4 )
        else:
            return ( (n + 3) / 4, 4 )

def set_fixed_size(window, w, h):
    window.SetSizeHints(w, h, w, h)

def init_menu(window, state):
    def make_dialog(dialog_constructor):
        def go(evt):
            dialog = dialog_constructor(window, state)
            if dialog.ShowModal() == wx.ID_OK:
                pass
            dialog.Close()
        return go

    def make_window(cons):
        def go(evt):
            win = cons(window, state)
            win.Show()
        return go

    def on_load(path):
        print state.path
        load_samples(state, path)        
        update_ui(window, state)

    def on_mute(evt):
        state.client.fade_out_and_stop_all(1)
        window.taps.clear_values()

    make_menu_bar(window, [
        menuItem('&File', [
            normalItem('Load', cbk = get_dir_dialog(on_load, defaultPath = state.path)),
            normalItem('Volumes', cbk = make_window(VolumeDialog)),
            normalItem('Mute', cbk = on_mute),
            normalItem('Bpms', cbk = make_dialog(BpmDialog)),
            normalItem('Settings', cbk = make_dialog(PrefDialog)),
            normalItem('Quit', cbk = lambda evt: window.Close())
        ])            
    ])

def to_linear_index(state, x, y):
    return state.size_x * y + x

def setup(frame, state):  
    init_ui(frame, state)    
    update_ui(frame, state)
    
    state.start_client(frame)
    init_close(frame, state)

def init_ui(frame, state):
    pnl = wx.Panel(frame)
    frame.pnl = pnl   
    pnl.SetFont(get_font()) 
    frame.taps = None 

def update_ui(frame, state):  

    def on_tap(x, y, is_on):
        index = to_linear_index(state, x, y)
        state.ons[index] = is_on
        if is_on:
            play_by_type(state.client, index, index, state.play_types[index], state.play_periods[index])            
        else:
            state.client.stop(index)

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
    init_menu(frame, state)


def init_close(frame, state):
    
    def on_close(evt):
        state.close()
        frame.Destroy()

    frame.Bind(wx.EVT_CLOSE, on_close)

 
key_rows = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']'],
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
        keycode = evt.GetUnicodeKey()        
        coord = get_key_coord(keycode)
        print "shift %s" % str(evt.ShiftDown())
        print keycode
        print coord
        if coord is not None:
            x, y = coord
            ix = to_linear_index(state, x, y)
            if x < state.size_x and y < state.size_y:
                if evt.ControlDown():
                    state.toggle_speed(ix)
                elif evt.ShiftDown():
                    state.boost_speed(ix)
                elif evt.AltDown():
                    state.slow_speed(ix)
                elif evt.MetaDown():
                    state.reset_speed(ix)
                else:
                    frame.taps.toggle(x, y)
        print keycode, coord

    print "Press bind"
    frame.taps.Bind(wx.EVT_KEY_DOWN, on_press)
    frame.taps.SetFocus()


class SamplerFrame(wx.Frame):
    def __init__(self, args, parent = None, id = -1, title = "Sampler", size = (WIDTH, HEIGHT)):
        state = St(args)
        wx.Frame.__init__(self, parent, id, title, size)
        setup(self, state)
        self.Centre()
        self.Show(True)
        self.state = state

        Publisher().subscribe(self.on_load, "sampler_load")
        Publisher().subscribe(self.on_stop, "sampler_stop")
        Publisher().subscribe(self.on_volume, "sampler_volume")

    def on_load(self, msg):
        path = msg.data[0]
        load_samples(self.state, path)
        update_ui(self, self.state)

    def on_stop(self, msg):        
        self.state.client.fade_out_and_stop_all(1)
        self.taps.set_values([False] * self.state.size)

    def on_volume(self, msg):
        volume = msg.data
        self.state.client.set_master_volume(volume)

class BpmDialog(wx.Dialog):
    def __init__(self, parent, state):
        wx.Dialog.__init__(self, parent, -1)

        x1 = 20
        x2 = 150
        dy = 35

        pnl = wx.Panel(self)    
        font = get_font()
        t1 = wx.StaticText(pnl, label="TODO", pos = (x1, 20))  
        t1.SetFont(font)  
        
        self.SetTitle("Bpms")        
        self.SetSize((270, 170))

class VolumeDialog(wx.Frame):
    def __init__(self, parent, state):
        size_x, size_y = state.size_x, state.size_y
        width  = int(size_x * float(270) / 4)
        height = int(size_y * float(170) / 2)

        wx.Frame.__init__(self, parent, -1, size = (width, height), title = "Volumes")

        pnl = wx.Panel(self)    
        font = get_font()        

        def on_volume(index):
            def go(x):
                state.volumes[index] = x
                state.client.set_volume(index, x)                
            return go

        def make_row(y):
            row = []
            for ix in range(size_x):
                index = to_linear_index(state, ix, y)
                row.append(Knob(pnl, state.volumes[index], cbk = on_volume(index)))
            return hor(row)

        sizer = ver([make_row(y) for y in range(size_y)])
        pnl.SetSizer(sizer)

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
        t3 = wx.StaticText(pnl, label="Tempo",   pos = (x1, 20 + 2 * dy))
        t4 = wx.StaticText(pnl, label="Volume",  pos = (x1, 20 + 3 * dy))   

        #t4 = wx.StaticText(pnl, label="Font",    pos = (x1, 20 + 3 * dy))   
        
        v1 = spin_ctrl(pnl, initial=state.port_out, min=0, max=100000, pos = (x2, 20))
        v3 = spin_ctrl(pnl, initial=state.tempo, min=40, max=300, pos = (x2, 20 + 2 * dy), cbk = lambda x: state.set_tempo(x))
        v4 = hor_slider(pnl, initial = 0.5, pos = (x2, 20 + 3 * dy), size = (100, -1), cbk = lambda x: state.set_master_volume(x))
        #v4 = spin_ctrl(pnl, initial=14, min=8, max=24, pos = (x2, 20 + 3 * dy))
        self.port_out = v1

        btn = wx.Button(pnl, label="Save", pos = (100, 20 + 4 * dy))
        pnl.Bind(wx.EVT_BUTTON, lambda evt: self.on_save(state, evt), btn)

        [t.SetFont(font) for t in [t1, t2, t3, t4, v1, v3, v4, btn]]

        self.SetTitle("Settings")        
        self.SetSize((270, 200))

    def on_save(self, state, evt):        
        port_out = self.port_out.GetValue()
        if (state.port_out != port_out):
            state.port_out = port_out
            state.start_client()
        state.save()
        self.Close()


def main():
    runApp(setup, 'sampler', size = (WIDTH, HEIGHT), state = St(parse_args()))

if __name__ == '__main__':
    main()
