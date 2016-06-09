import OSC, threading, time

class OscServer:
    def __init__(self, port, cbks = None):
        self.server = OSC.OSCServer( ("localhost", port) )
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
            s.close()
            print "Waiting for Server-thread to finish"
            st.join()
            print "Done"


    def close(self):
        self.server.close()    
        try:
            self.thread.join()
        except:
            pass
        print "Done"


def _msg(addr, *names):
    oscmsg = OSC.OSCMessage()
    oscmsg.setAddress(addr)
    for name in names:
        oscmsg.append(name)    
    return oscmsg

class OscClient:
    def __init__(self, port):
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', port))

    def send(self, addr, *args):
        try:        
            self.client.send(_msg(addr, *args))
        except OSC.OSCClientError:
            print "No one listens for OSC"

