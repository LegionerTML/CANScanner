import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import datetime
from threading import Thread
import os
from ctypes import *
#from CANLoaderController import CANLoaderController, CANLoaderFirmwareVerifyException, CANLoaderDeviceFailureException
import queue
from CANFoxLib import CANFoxLibSkin, CANfoxException, CANfoxHardwareException
from enum import *
import settings
import platform
import CANTypeDefs
import tkinter.ttk as ttk
from ThreadCANMsgReader import ThreadCANMsgReader

if platform.architecture()[0] == '32bit':
    from sieca132_client_x32 import sieca132_client
else:
    from sieca132_client_x64 import sieca132_client

import CANLoaderAbout



class Table(tk.Frame):
    def __init__(self, parent=None, headings=tuple()):
        super().__init__(parent)

        self.table = ttk.Treeview(self, displaycolumns="#all", show="headings", selectmode="browse")
        self.table["columns"]=headings
        self.table["displaycolumns"]=headings

        for head in headings:
            self.table.heading(head, text=head, anchor=tk.CENTER)
            self.table.column(head, anchor=tk.CENTER, stretch=True)

        scrolltable = tk.Scrollbar(self, command=self.table.yview)
        self.table.configure(yscrollcommand=scrolltable.set)
        scrolltable.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(expand=tk.YES, fill=tk.BOTH)
    def add(self, row=tuple()):
        id = self.table.insert('', tk.END, values=tuple(row))
        return id
    def update(self, id, row):
        #id = self.table.identify_row(y=number)

        self.table.item(item=id, values=tuple(row))
        return

class MainApplication(tk.Frame):
    def __init__(self, master = None):
        self.master = master
        tk.Frame.__init__(self, master)
        self.init_window()
        self.id1 = []

    def __add_log_msg__(self, message):
        self.flLstResults.insert(tk.END, "[" + datetime.datetime.now().strftime("%H:%M:%S")+"] " + message)
        self.flLstResults.yview(tk.END)
        return

    def init_window(self):
        defaultMainWindowSizeX = 800
        defaultMainWindowSizeY = 600


        self.master.title("CAN Scanner v0.0.1")
        self.master.minsize(500, 400)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))

        tkMenu = Menu(self.master)
        self.master.config(menu=tkMenu)
        tkMenuItemFile = Menu(tkMenu, tearoff=0)
        tkMenu.add_cascade(label="Program", menu=tkMenuItemFile)
        tkMenuItemFile.add_command(label="Connect", command=lambda: self.buttonConnectClick())
        tkMenuItemFile.add_command(label="Add", command=lambda: self.buttonAddClick())

        self.table = Table(self.master, headings=('ID', 'Data', 'Len', 'Extended'))
        self.table.pack(expand=tk.YES, fill=tk.BOTH)

        '''self.frameLog = tk.LabelFrame(self.master, relief=tk.RAISED, borderwidth=1, text="Log")
        self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameLog.columnconfigure(0, weight=20, pad=3)
        self.frameLog.columnconfigure(1, weight=20, pad=3)
        self.frameLog.rowconfigure(0, weight=1, pad=3)
        


        self.flLstResults = tk.Listbox(self.master, height=20, width = 100)
        self.flLstResults.grid(row=0, column=0)

        
        self.flLstResults = tk.Listbox(width=20, height=20)
        #self.flLstResults.pack()
        #self.flLstResults.config(height=20, width=20)
        self.flLstResults.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.__add_log_msg__("self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)")'''
        #buttonConnect = tk.Button(self.master, state="normal", text=r"Connect", command=self.buttonCANConnectClick)
        #buttonConnect.grid()
        #buttonConnect.pack()
        '''label1 = tk.Label(self.master, text="Button: ")
        label1.grid(column=10, row=1)
        label2 = tk.Label(self.master, text="2")
        label2.grid(column=5, row=5)'''
        self.master.mainloop()

    def buttonAddClick(self):
        #add and update row in the table
        id = self.table.add((9, 8, 7, 6))
        self.table.update(id, (3, 4, 9, 8))
        return

    def check_my_msg(self):
        i = 0
        while i<30:
            d_retval = self.sieca_lib.canRead(self.siecaLibHandle)

            for item in range(0, d_retval["l_len"].value):
                msg1 = d_retval["canmsg"][item]
        # msg2 = d_retval["canmsg"][0]
            s_data = ""
        # s_data = msg1.aby_data
            for y in range(0, msg1.by_len):
                s_data += str(hex(msg1.aby_data[y])) + " "
            self.table.add((hex(msg1.l_id), s_data, msg1.by_len, msg1.by_extended))
            i += 1

        #self.master.after(100, self.check_my_msg)

    def buttonConnectClick(self):
        self.sieca_lib = sieca132_client()

        l_netnumber = 105
        l_txtimeout = -1
        l_rxtimeout = -1

        c_canAppName = "canAppName"
        c_ReceiverEventName = "RE1"
        c_ErrorEventName = "EE1"

        d_retval = self.sieca_lib.canOpen(l_netnumber, 0, 0, l_txtimeout, l_rxtimeout, c_canAppName,
                                          c_ReceiverEventName, c_ErrorEventName)
        # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(d_retval["l_retval"]), d_retval["handle"])
        self.siecaLibHandle = d_retval["handle"]
        # siecaDllInfo = CANTypeDefs.st_InternalDLLInformation()
        # res = self.sieca_lib.canGetDllInfo(ctypes.addressof(siecaDllInfo))
        #self.flLstResults.insert(tk.END, "sieca_lib: " + str(self.sieca_lib))
        # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(res))
        # self.flLstResults.insert(tk.END, siecaDllInfo.aui_TxCounter)

        l_retval = self.sieca_lib.canSetBaudrate(self.siecaLibHandle,
                                                 int(CANTypeDefs.Baudrate.BAUD_250))  # 250 kbits/sec
        #self.flLstResults.insert(tk.END, "Set Baudrate: " + str(CANTypeDefs.ReturnValues(l_retval)))
        l_retval = self.sieca_lib.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
        #self.flLstResults.insert(tk.END, "LED flashing settings applied: " + str(CANTypeDefs.ReturnValues(l_retval)))
        l_retval = self.sieca_lib.canIsNetOwner(d_retval["handle"])
        #self.flLstResults.insert(tk.END, "CanIsNetOwner: " + str(CANTypeDefs.ReturnValues(l_retval)))

        l_retval = self.sieca_lib.canSetFilterMode(self.siecaLibHandle, CANTypeDefs.T_FILTER_MODE.filterMode_nofilter)
        #self.flLstResults.insert(tk.END, "CanSetFilterMode: " + str(CANTypeDefs.ReturnValues(l_retval)))
        #message_reader = ThreadCANMsgReader(self.siecaLibHandle, self.sieca_lib, self.QueueIncomingMessages)
        #message_reader.start()

        # d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
        # self.flLstResults.insert(tk.END, "DataCount: " + str(d_retval["l_len"]))
        # self.flLstResults.insert(tk.END, "DataCount: " + str(CANTypeDefs.ReturnValues(d_retval["l_retval"])))

        '''d_retval = self.sieca_lib.canRead(self.canfox_handle)
        for item in range(0, d_retval["l_len"].value):
            self.queue.put(d_retval["canmsg"][item])'''
        self.check_my_msg()
        '''i = 0
        while i < 10:
            d_retval = self.sieca_lib.canRead(self.siecaLibHandle)


            for item in range(0, d_retval["l_len"].value):
                msg1 = d_retval["canmsg"][item]
            #msg2 = d_retval["canmsg"][0]
            s_data = ""
            #s_data = msg1.aby_data
            for y in range(0, msg1.by_len):
                s_data += str(hex(msg1.aby_data[y])) + " "
            self.__add_log_msg__("[" + str(hex(msg1.l_id)) + "] Data = " + s_data + "; Len = " + str(msg1.by_len) + "; Ext: " + str(msg1.by_extended) + ";")
            i += 1'''

        # self.process_queue()

        return

def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()