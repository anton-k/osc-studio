import wx, osc, glob, os.path, json, argparse, knob, toggle_matrix, unicodedata
from wx_utils import *
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from ui_rnd_tap import TapFrame, TapArgs
from ui_sampler import SamplerFrame, SamplerArgs
from ui_flow import FlowFrame, FlowArgs

from wx.lib.pubsub import Publisher

FONT_SIZE = 14
ON_COLOR = '#00AA55'
OFF_COLOR = '#000000'

FLOW_PORT = 7700
SAMPLER_PORT = 7701
TAP_PORT = 7702

FLOW_NAME = 'flow'
SAMPLER_NAME = 'sampler'
TAP_NAME = 'tap'

def unicode2string(x):
    return unicodedata.normalize('NFKD', x).encode('ascii','ignore')

def get_font():
    font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    font.SetPointSize(FONT_SIZE)        
    return font

def parse_args():
    parser = argparse.ArgumentParser(description="UI for flow audio server.")
    parser.add_argument('--path', dest='path', type=str, nargs='?', help = 'Path to load.')
    args = parser.parse_args()
    return args.path

class St:
    def __init__(self):
        path = parse_args()

        if os.path.isfile(path):
            with open(path, "r") as myfile:
                 tracks = json.load(myfile) 

            self.items =  tracks.get('tracks', [])
        else:
            self.items = []

        self.path = os.path.dirname(path)
        self.selected = 0
        self.is_on = False

class TrackList(wx.Frame):
    def __init__(self, state):
        self.init_parent_frame()
        self.init_audio_units()
        self.set_state(state)        
        self.init_widgets()
        self.select_track()        

    def init_parent_frame(self):
        wx.Frame.__init__(self, None, -1, title = "Track list", size =  (250, 500))

    def set_state(self, state):
        self.state = state

    def set_font(self):
        font = get_font()
        for widget in [self.prev, self.next, self.play, self.tracks]:
            widget.SetFont(font)

    def init_audio_units(self):
        self.init_flow()
        self.init_sampler()
        self.init_tap()

    def init_flow(self):
        self.flow_window = self.make_audio_unit_window(FlowFrame, FlowArgs, FLOW_PORT)
        self.flow_client = self.make_audio_unit_client(FLOW_NAME)

    def init_sampler(self):
        self.sampler_window = self.make_audio_unit_window(SamplerFrame, SamplerArgs, SAMPLER_PORT)
        self.sampler_client = self.make_audio_unit_client(SAMPLER_NAME)

    def init_tap(self):
        self.tap_window = self.make_audio_unit_window(TapFrame, TapArgs, TAP_PORT)
        self.tap_client = self.make_audio_unit_client(TAP_NAME)

    def init_audio_unit(self, make_frame, make_args, name, port):        
        window = make_frame(make_args(port_out = port), parent = self)
        client = AudioUnit(name)
        return window, client

    def make_audio_unit_window(self, make_frame, make_args, port):
        return make_frame(make_args(port_out = port), parent = self)

    def make_audio_unit_client(self, name):
        return AudioUnit(name)


    #-------------------------------------------------------------------
    # Widgets

    def init_navigation_and_tracks(self):
        self.buttons = self.make_navigation_bar()
        self.tracks = self.make_tracks()

    def init_widgets(self):   
        self.init_navigation_and_tracks()
        layout = ver([Cell(self.buttons, 1), Cell(hor([self.tracks]), 15)])
        self.SetSizer(layout)
        self.set_font()

    # Navigation bar

    def make_play_button(self):
        return button(self, "On", cbk = self.on_play)

    def make_prev_button(self):
        return button(self, "<<", cbk = self.on_prev)

    def make_next_button(self):
        return button(self, ">>", cbk = self.on_next)

    def make_navigation_bar(self):
        self.play = self.make_play_button()
        self.prev = self.make_prev_button()
        self.next = self.make_next_button()
        buttons = hor([self.play, self.prev, self.next])
        return buttons

    def select_track(self):
        self.tracks.Focus(self.state.selected)
        self.tracks.Select(self.state.selected)                

    def unselect_track(self):
        self.tracks.Focus(self.state.selected)
        self.tracks.Select(self.state.selected, on = 0)

    def on_prev(self, evt):
        self.unselect_track()        
        n = self.state.selected
        if n == 0:
            self.state.selected = len(self.state.items) - 1
        else:
            self.state.selected = n - 1
        self.select_track()        

    def on_next(self, evt):
        self.unselect_track()        
        n = self.state.selected
        if n == len(self.state.items) - 1:
            self.state.selected = 0
        else:
            self.state.selected = n + 1
        self.select_track() 

    def set_color(self, col):
        self.play.SetForegroundColour(col)
        self.prev.SetForegroundColour(col)
        self.next.SetForegroundColour(col)

    def on_play(self, evt):
        self.state.is_on = not(self.state.is_on)
        if self.state.is_on:
            self.play.SetLabel("On")
            self.set_color(ON_COLOR)
        else:
            self.play.SetLabel("Off")
            self.set_color(OFF_COLOR)

    # Track list

    def make_tracks(self):
        tracks = wx.ListCtrl(self)        
        tracks.InsertColumn(0, 'Tracks', width = 200)
        tracks.SetColumnWidth(0,  wx.LIST_AUTOSIZE)
        items = self.state.items[:]
        items.reverse()
        for s in items:
            tracks.InsertStringItem(0, s)        
        tracks.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_track_selected)
        return tracks

    def get_dir(self, name, client):            
        return os.path.join(self.state.path, name, client)

    def on_track_selected(self, evt): 
        self.update_selection(evt)
        path = self.get_selected_path(evt)   
        self.load_clients(path)

    def load_clients(self, path):
        self.flow_client.load(path)
        self.sampler_client.load(path)
        self.tap_client.load(path)

    def update_selection(self, evt):
        currentItem = evt.m_itemIndex 
        self.state.selected = currentItem      

    def get_selected_name(self, evt):
        currentItem = evt.m_itemIndex        
        return self.state.items[currentItem]

    def get_selected_path(self, evt):
        return os.path.join(self.state.path, self.get_selected_name(evt))

    #-------------------------------------------------------------------

class AudioUnit:
    def __init__(self, name):
        self.client = Client()
        self.name = name

    def get_client_path(self, path):
        print "PATH %s" % repr(path)
        return os.path.join(path, unicode(self.name))

    def load(self, path):
        client_path = self.get_client_path(path)
        if (os.path.isdir(client_path)):
            self.client.send(self.name, 'load', client_path)
        else:
            self.stop()

    def start(self):
        self.client.send(self.name, 'start')

    def stop(self):
        self.client.send(self.name, 'stop')

    def set_volume(self, volume):
        self.client.send(self.name, 'set_volume', volume)

class Client:
    def __init__(self):
        self.client = Publisher()

    def send(self, audio_unit, action, *msgs):
        address = "%s_%s" % (audio_unit, action)
        print "TO %s SEND %s" % (address, repr(msgs))
        self.client.sendMessage(address, msgs)


        
def runApp(state):
    app = wx.App()
    TrackList
    frame = TrackList(state)
    frame.Centre()
    frame.Show(True)
    app.MainLoop()  

def main():
    state = St()
    runApp(state)

if __name__ == "__main__":
    main()