import wx

light_gray_color = "#AAAAAA"
primary_color = "#B755C7"
OFFSET = 2
RECT_RAD = 5

class ToggleMatrix(wx.Panel):
    def __init__(self, parent, size, names = None, cbk = None, init_values = None, widget_size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, -1, size = widget_size)
        self.matrix_szie_x = size[0]
        self.matrix_szie_y = size[1]
        if names is None:
            self.names = []
        else:
            self.names = names

        self.cbk = cbk

        if init_values is None:       
            self.values = [False] * (self.matrix_szie_x * self.matrix_szie_y)       
        else:
            self.values = init_values

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)     

        self.primary_brush = wx.Brush(primary_color, style=wx.SOLID)
        self.secondary_brush = wx.Brush(light_gray_color, style=wx.SOLID)

    def set_cbk(self, cbk):
        self.cbk = cbk   

    def set_names(self, names):
        self.names = names
        self.Refresh()

    def toggle(self, nx, ny):
        ix = self.get_linear_index(nx, ny)        
        self.values[ix] = not(self.values[ix])
        if self.cbk is not None:
            self.cbk(nx, ny, self.values[ix])
        self.Refresh()   

    def toggle_with_linear_index(self, index):
        self.toggle(*self.from_linear_index(index))

    def on_paint(self, event):
        w, h = self.GetSize()  
        dx = w / self.matrix_szie_x        
        dy = h / self.matrix_szie_y        
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen(primary_color, style=wx.TRANSPARENT))
        dc.SetFont(self.GetFont())
        for i in range(self.matrix_szie_x):
            for j in range(self.matrix_szie_y):
                ix = self.get_linear_index(i, j)
                if self.values[ix]:
                    dc.SetBrush(self.primary_brush)
                else:
                    dc.SetBrush(self.secondary_brush)
                dc.DrawRoundedRectangle(dx * i + OFFSET, dy * j + OFFSET, dx - 2 * OFFSET, dy - 2 * OFFSET, RECT_RAD)

                if (ix < len(self.names)):
                    text = self.names[ix]
                    tw, th = dc.GetTextExtent(text)
                    dc.DrawText(text, dx * (i + 0.5) - tw/2, dy * (j + 0.5) - th/2)

    def on_click(self, event):
        nx, ny = self.get_rect(event.GetX(), event.GetY())
        self.toggle(nx, ny)
              

    def on_size(self, event):
        self.Refresh()

    def get_rect(self, x, y):
        w, h = self.GetSize() 
        nx = int(self.matrix_szie_x * float(x) / w)
        ny = int(self.matrix_szie_y * float(y) / h)
        return nx, ny

    def get_index(self, x, y):
        nx, ny = self.get_rect(x, y)
        return self.get_linear_index(nx, ny)

    def get_linear_index(self, nx, ny):
        return ny * self.matrix_szie_x + nx

    def from_linear_index(self, index):
        nx = index % self.matrix_szie_x
        ny = int(index / self.matrix_szie_x)
        return nx, ny