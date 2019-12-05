import threading
from sieca132_client_x64 import sieca132_client
from queue import Queue
import time

class ThreadCANMsgReader(threading.Thread):
    def __init__(self, handle, lib, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sieca_lib = lib
        self.canfox_handle = handle

    def run(self):
        while 1:
            #time.sleep(0.1)
            d_retval = self.sieca_lib.canRead(self.canfox_handle)
            for item in range(0, d_retval["l_len"].value):
                self.queue.put(d_retval["canmsg"][item])

