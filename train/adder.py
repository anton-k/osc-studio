from OSC import OSCServer
import sys
import time, threading

#server = OSCServer( ("localhost", 7110) )

class OscServer:
    def __init__(self, port, cbks = None):
        self.server = OSCServer( ("localhost", port) )
        self.server.addDefaultHandlers()
        self.thread = threading.Thread(target = self.server.serve_forever)

        if cbks is not None:
            for path, cbk in cbks:
                self.on_msg(path, cbk)

    def on_msg(self, path, f):
        def go_zero(path, tags, args, source):
            f()            

        def go_args(path, tags, args, source):
            f(*args)

        if f.func_code.co_argcount == 0:
            go = go_zero
        else:
            go = go_args

        self.server.addMsgHandler(path, go)

    def start(self):
        self.thread.start()
        try :
            while 1 :
                time.sleep(10) 
        except KeyboardInterrupt :
            print "\nClosing OSCServer."
            self.server.close()
            print "Waiting for Server-thread to finish"
            self.thread.join()
            print "Done"

    def close(self):
        self.server.close()    
        try:
            self.thread.join()
        except:
            pass
        print "Done"

class Counter:
    def __init__(self):
        self.count = 0

    def add(self, n):
        self.count += n

    def show(self):
        print self.count


counter = Counter()
server = OscServer(7110)

def print_cbk(n):
    print n

def show_cbk():
    counter.show()

def add_cbk(n):
    counter.add(n)

def on_quit():
    server.close()

server.on_msg("/echo", print_cbk)
server.on_msg("/show", show_cbk)
server.on_msg("/add", add_cbk)
server.on_msg("/quit", on_quit)

server.start()

# st = threading.Thread(target = server.serve_forever)

# def on_quit(path, tags, args, source):    
#     server.close()    
#     try:
#         st.join()
#     except:
#         pass
#     print "Done"



# server.addDefaultHandlers()
# server.addMsgHandler("/echo", print_cbk)
# server.addMsgHandler("/show", show_cbk)
# server.addMsgHandler("/add", add_cbk)
# server.addMsgHandler("/quit", on_quit)

# st.start()