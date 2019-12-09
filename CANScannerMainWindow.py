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

class RxData:
    def __init__(self):
        self.list1 = []

    def add(self, row):
        #index = self.list1.index(row[1])
        #a = str(row[0])
        ret, id_n, ii = self.find(row[1])
        if ret is True:
            self.update(ii, row[2], row[3])
        else:
            self.list1.append(row)

        return row

    def find(self, id_s):
        ret = False
        id_n = 0
        ii = 0
        for i in range(len(self.list1)):
            if self.list1[i][1] == id_s:
                ret = True
                id_n = self.list1[i][0]
                ii = i
                break
        return ret, id_n, ii

    def update(self, num, s_data, s_len):
        self.list1[num][2] = s_data
        self.list1[num][3] = s_len
        self.list1[num][4] = self.list1[num][4] + 1
        return 0

    def get(self, i):
        return self.list1[i]

    def getall(self):
        return self.list1

    def clear(self):
        self.list1.clear()
        return

class Table(tk.Frame):
    def __init__(self, parent=None, headings=tuple()):
        super().__init__(parent)

        self.table = ttk.Treeview(self, displaycolumns="#all", show="headings", selectmode="browse")
        self.table["columns"]=headings
        self.table["displaycolumns"]=headings

        for head in headings:
            self.table.heading(head, text=head, anchor=tk.CENTER)
            if head == 'Len':
                self.table.column(head, anchor=tk.CENTER, stretch=False, width=50)

            else:
                if head == 'Count':
                    self.table.column(head, anchor=tk.CENTER, stretch=True, width=50)
                else:
                    if head == 'Data':
                        self.table.column(head, anchor=tk.CENTER, stretch=True, width=300)
                    else:
                        self.table.column(head, anchor=tk.CENTER, stretch=True, width=50)


        scrolltable = tk.Scrollbar(self, command=self.table.yview)
        self.table.configure(yscrollcommand=scrolltable.set)
        scrolltable.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(expand=tk.YES, fill=tk.BOTH)

    def add(self, row=tuple()):
        id_s = self.table.insert('', tk.END, values=tuple(row))
        return id_s

    def update(self, id_s, row):
        self.table.item(item=id_s, values=tuple(row))
        return

    def check(self, i):

        row = ()
        ret = self.table.identify_element(x=1, y=2)
        #if ret == 2:
        id_s = self.table.identify_row(1)
        row = (self.table.identify_element(2, 0), self.table.identify_element(2, 1), self.table.identify_element(2, 2), 3)
        #row[0] = self.table.identify_element(2, 0)
        #row[1] = self.table.identify_element(2, 1)
        #row[2] = self.table.identify_element(2, 2)
        #row[3] = 3
        self.table.item(item=self.table.identify_row(y=1), values=tuple(row))
        #self.table.item(item=i, values=tuple(row))
        return ret, row, self.table.identify_row(y=1), i

class MainApplication(tk.Frame):
    def __init__(self, master = None):
        self.master = master
        tk.Frame.__init__(self, master)
        self.init_window()
        self.is_can_close = True
        self.id1 = []

    def __add_log_msg__(self, message):
        self.flLstResults.insert(tk.END, "[" + datetime.datetime.now().strftime("%H:%M:%S")+"] " + message)
        self.flLstResults.yview(tk.END)
        return

    def init_window(self):
        defaultMainWindowSizeX = 820
        defaultMainWindowSizeY = 600


        self.master.title("CAN Scanner v0.0.1")
        self.master.minsize(500, 400)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))

        tkMenu = Menu(self.master)
        self.master.config(menu=tkMenu)
        tkMenuItemFile = Menu(tkMenu, tearoff=0)
        tkMenu.add_cascade(label="Program", menu=tkMenuItemFile)
        tkMenuItemFile.add_command(label="Connect", command=lambda: self.buttonConnectClick())
        #tkMenuItemFile.add_command(label="Add", command=lambda: self.buttonAddClick())
        tkMenuItemFile.add_command(label="Disconnect", command=lambda: self.buttonDisconnectClick())
        self.data = RxData()
        self.table = Table(self.master, headings=('ID', 'Data', 'Len', 'Count'))
        self.table.pack(expand=tk.YES, fill=tk.BOTH)
        #self.table.add((0, 0, 0, 0))
        #self.table.add((1, 1, 1, 1))
        #self.table.add((2, 2, 2, 2))

        '''self.frameLog = tk.LabelFrame(self.master, relief=tk.RAISED, borderwidth=1, text="Log")
        #self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameLog.columnconfigure(0, weight=20, pad=3)
        self.frameLog.columnconfigure(1, weight=20, pad=3)
        self.frameLog.rowconfigure(0, weight=1, pad=3)
        


        self.flLstResults = tk.Listbox(self.master, height=20, width = 100)
        self.flLstResults.pack()'''

        

        #self.__add_log_msg__("self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)")
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
        '''id = self.table.add((9, 8, 7, 6))
        self.table.update(id, (3, 4, 9, 8))
        i1, i2, i3, i4 = self.table.check(id)'''
        row1 = [1, 1, [1, 2, 3, 4, 5, 6, 7, 8], 1, 1]
        row2 = [2, 2, 2, 2, 2]
        row3 = [3, 3, 3, 3, 3]
        row4 = [4, 2, 4, 4, 3]
        in1 = self.data.add(row1)
        in2 = self.data.add(row2)
        in3 = self.data.add(row3)
        in4 = self.data.add(row4)
        list = self.data.get()
        self.__add_log_msg__(str(in3) + " " + str(row2[1]) + " " + str(row3[1]) + " " + str(row4[1]))
        for i in range(len(list)):
            self.__add_log_msg__(str(list[i]))

        return

    def check_my_msg(self):
        #i = 0
        #while i<30:
        d_retval = self.sieca_lib.canRead(self.siecaLibHandle)

        for item in range(0, d_retval["l_len"].value):
            msg1 = d_retval["canmsg"][item]
        # msg2 = d_retval["canmsg"][0]
        s_data = ""
        # s_data = msg1.aby_data
        for y in range(0, msg1.by_len):
            s_data += str(hex(msg1.aby_data[y])) + " "
        flagF, id_n, num = self.data.find(msg1.l_id)
        if flagF is False:
            if msg1.l_id != 0:
                id_s = self.table.add((hex(msg1.l_id), s_data, msg1.by_len, 1))
                row = [id_s, msg1.l_id, s_data, msg1.by_len, 1]
                self.data.add(row)
        else:
            self.data.update(num, s_data, msg1.by_len)
            get_row = self.data.get(num)
            self.table.update(id_n, (hex(get_row[1]), get_row[2], get_row[3], get_row[4]))
            #i += 1

        #self.flLstResults.delete(0, tk.END)

        '''list_s = self.data.getall()
        for i in range(len(list_s)):
            self.__add_log_msg__(str(list_s[i]))'''
        if self.is_can_close is False:
            self.master.after_idle(self.check_my_msg)
        else:
            return

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
        self.is_can_close = False
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

    def buttonDisconnectClick(self):
        l_retval = self.sieca_lib.canClose(self.siecaLibHandle)
        self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(l_retval))
        self.is_can_close = True
        return

def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()