import math
import wx

light_gray_color = "#AAAAAA"
primary_color = "#A444A4"

def within(x, a, b):
    return min(max(x, a), b)

value_offset = 0.1

class Knob(wx.Panel):
    def __init__(self, parent, value = 0.5, cbk = None):
        wx.Panel.__init__(self, parent, -1)
        self.prev_value = value
        self.value = value
        self.cbk = cbk
        self.is_touch = False

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)        
        self.Bind(wx.EVT_MOTION, self.on_motion)

    def set_cbk(self, cbk):
        self.cbk = cbk

    def on_paint(self, event):
        width = 14
        self.draw_circle(light_gray_color, width)
        self.draw_arc(-0.75 + value_offset + 0.01 + self.value * (1 - 2 * value_offset), 0.25 + value_offset, primary_color, width)

    def draw_circle(self, color, width = 5):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
        pen = wx.Pen(color,style=wx.SOLID)     
        pen.SetWidth(width)
        dc.SetPen(pen)     

        w, h = self.GetSize() 
        cx = w / 2
        cy = h / 2
        rad = min(w/2, h/2) - width - 1
        dc.DrawCircle(cx, cy, rad)

    def draw_arc(self, a1, a2, color, width = 5):        
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
        pen = wx.Pen(color,style=wx.SOLID)     
        pen.SetWidth(width)
        dc.SetPen(pen)     

        w, h = self.GetSize() 
        cx = w / 2
        cy = h / 2
        rad = min(w/2, h/2) - width - 1

        def getX(a):
            return cx + rad * math.cos(2 * math.pi * a)

        def getY(a):
            return cy + rad * math.sin(2 * math.pi * a)

        dc.DrawArc(getX(a1), getY(a1), getX(a2), getY(a2), cx, cy)

    def on_click(self, event):
        self.is_touch = not(self.is_touch)
        if self.is_touch:            
            self.track_volume(event.GetX(), event.GetY(), allow_jumps = True)
            self.Refresh()

    def on_motion(self, event):
        if self.is_touch:
            self.track_volume(event.GetX(), event.GetY(), allow_jumps = False)            
            self.Refresh()

    def track_volume(self, x, y, allow_jumps):         
        w, h = self.GetSize() 
        x0 = w / 2
        y0 = h / 2
        t1 = within((math.atan2(x - x0, - y + y0) / (2 * math.pi)) + 0.5, value_offset, 1 - value_offset)
        t  = (t1 - value_offset) / (1 - 2 * value_offset)
        if not(not allow_jumps and abs(t - self.prev_value) > 0.2):
            self.prev_value = self.value
            self.value = t
        else:
            self.prev_value = self.value

        if self.cbk is not None:
            self.cbk(self.value)

    def on_size(self, event):
        self.Refresh()

