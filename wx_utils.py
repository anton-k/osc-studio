import wx

# -------------------------------------------------
# App utils

def runApp(setup, title = '', size = None, state = None):
    app = wx.App()
    frame = wx.Frame(None, -1, title)
    if state is not None:
        setup(frame, state)
    else:
        setup(frame)
    frame.Centre()
    if size:
        frame.SetSize(size)
    frame.Show(True)
    app.MainLoop()    

# -------------------------------------------------
# Menu utils

class Item():
    def __init__(self, title, cbk = None, kind = wx.ITEM_NORMAL, children = [], is_check = None):
        self.title = title
        self.cbk   = cbk
        self.kind  = kind
        self.children = children
        self.is_check = is_check

def radioItem(title, cbk = None, is_check = None):
    return Item(title, cbk, wx.ITEM_RADIO, [], is_check)

def normalItem(title, cbk = None):
    return Item(title, cbk, wx.ITEM_NORMAL)

def echoPress(label):
    def go(evt):
        print ("Pressed %s" % label)    
    return go

def echoNormalItem(title):
    return normalItem(title, cbk = echoPress(title))

def echoCheckItem(title):
    return checkItem(title, cbk = echoPress(title))

def echoRadioItem(title):
    return radioItem(title, cbk = echoPress(title))

def checkItem(title, cbk = None, is_check = None):
    return Item(title, cbk, wx.ITEM_CHECK, [], is_check)

def menuItem(title, items):
    return Item(title, children = items)

def mkItem(root, parent, item):
    x = wx.MenuItem(parent, wx.ID_ANY, item.title, kind=item.kind)
    parent.AppendItem(x)
    if item.is_check is not None:
        x.Check(check = item.is_check)
    root.Bind(wx.EVT_MENU, item.cbk, x)

def mkMenu(root, menubar, title, items):
    res = wx.Menu()
    for item in items:
        if item.children:
            mkSubMenu(root, res, item.title, item.children)
        else:
            mkItem(root, res, item)            
    menubar.Append(res, title)
    return res

def mkSubMenu(root, parent, title, items):
    submenu = wx.Menu()
    for item in items:
        mkItem(root, submenu, item)                
    parent.AppendMenu(wx.ID_ANY, title, submenu)

def make_menu_bar(frame, items):
    menubar = wx.MenuBar()
    for item in items:
        mkMenu(frame, menubar, item.title, item.children)
    frame.SetMenuBar(menubar)

# -------------------------------------------------
# layout utils

class Cell():
    def __init__(self, item, scale = 1, flags = wx.EXPAND | wx.ALL, border = 0):
        self.item = item
        self.scale = scale
        self.flags = flags
        self.border = border

def box(orient, xs):
    box = wx.BoxSizer(orient)
    for x in xs:
        if not isinstance(x, Cell):
            x = Cell(x)
        box.Add(x.item, x.scale, x.flags, x.border)        
    return box

def reset_sizer(box, items):
    box.Clear(True)
    for x in items:
        if not isinstance(x, Cell):
            x = Cell(x)
        box.Add(x.item, x.scale, x.flags, x.border)

def hor(xs):
    return box(wx.HORIZONTAL, xs)

def ver(xs):
    return box(wx.VERTICAL, xs)

def unCell(x):
    if isinstance(x, Cell):
        return (x.item, x.scale, x.flags)
    else:
        return unCell(Cell(x))

def grid(rows, cols, vgap, hgap, xs):
    gs = wx.GridSizer(rows, cols, vgap, hgap)
    gs.AddMany([unCell(x) for x in xs])
    return gs

# ----------------------------------------------------------
# Dialogs

def get_dir_dialog(cbk, defaultPath = wx.EmptyString):
    def go(evt):
        dialog = wx.DirDialog(None, "Choose a directory:", defaultPath = defaultPath, style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath() 
            cbk(path)
        dialog.Destroy()
    return go

def ok_dialog(msg, title = ""):
    dial = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_ERROR)
    dial.ShowModal()

# Preferences 

class IntPref:
    def __init__(self, name, default, min_value, max_value):
        self.name = name
        self.default = default
        self.min_value = min_value
        self.max_value = max_value

    def render(self, parent, pos, group, config):
        def cbk(value):
            config.set(group, self.name)
        #static_text(parent, self.name, (10, pos[1]))
        #spin_ctrl(parent, self.default, pos = pos, size = (40, 20), self.min_value, self.max_value, cbk)        

class FloatPref:
    def __init__(self, name, default, min_value, max_value):
        self.name = name
        self.default = default
        self.min_value = min_value
        self.max_value = max_value


class StrPref:
    def __init__(self, name, default):
        self.name = name
        self.default = default

class ColorPref:
    def __init__(self, name, default):
        self.name = name
        self.default = default

class PrefGroup:
    def __init__(self, name, items):
        self.name = name
        self.items = items
 
class PrefDialog(wx.Dialog):
    def __init__(self, title, pref_groups):
        wx.Dialog.__init__(self, parent, -1, title)



class PrefConfig:
    def __init__(self):
        pass

    def get(self, group, name):
        pass

    def set(self, group, name):
        pass

    def write(self, group, name):
        pass

    def load(self):
        pass

def pref_dialog(pref_groups):
    pass

def pref_config(pref_groups):
    pass

# ----------------------------------------------------------
# Widgets

def button(root, title, cbk):
    b = wx.Button(root, wx.ID_ANY, title)
    root.Bind(wx.EVT_BUTTON, cbk, b)
    return b    

def staticText(root, title, font = None):
    res = wx.StaticText(root, wx.ID_ANY, title, style = wx.ALIGN_CENTRE)
    if font:
        res.SetFont(font)
    return res

def spin_ctrl(root, initial = 0, pos=wx.DefaultPosition, size=wx.DefaultSize, min=0, max=100, cbk = None):
    text = wx.SpinCtrl(root, value = str(initial), initial = initial, pos = pos, size = size, min = min, max = max)

    def go(event):
        cbk(text.GetValue())

    if cbk is not None:
        root.Bind(wx.EVT_TEXT, go, text)

    return text

def hor_slider(root, initial = 0, pos=wx.DefaultPosition, size=wx.DefaultSize, cbk=None):
    min = 0 
    max = 1000
    res = wx.Slider(root, value = initial * max, minValue = min, maxValue = max, pos = pos, size = size, style = wx.SL_HORIZONTAL)

    def go(event):
        cbk(float(res.GetValue() - min) / (max - min) )

    if cbk is not None:
        root.Bind(wx.EVT_SLIDER, go, res)

    return res


