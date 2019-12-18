import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import datetime
import platform
import CANTypeDefs
import tkinter.ttk as ttk
import os
import threading
import time

#if platform.architecture()[0] == '32bit':
from sieca132_client_x32 import sieca132_client
#else:
#   from sieca132_client_x64 import sieca132_client

view_p = 2
yview_listbox = '0'




def openDescriptionEvent(event):
    pass

def view_event_up(event):
    global yview_listbox, view_p
    yview_listbox = '0'
    view_p = 0

def view_event_down(event):
    global yview_listbox, view_p
    yview_listbox = tk.END
    view_p = 1

def view_event_scroll(event):
    global view_p, yview_listbox
    if view_p == 1:
        view_p = 0
        yview_listbox = '0'
    else:
        if view_p == 0:
            view_p = 1
            yview_listbox = tk.END

class threadRead(threading.Thread):
    def __init__(self, handle, lib):
        threading.Thread.__init__(self)
        self.Canhandle = handle
        self.sieca_lib = lib
        self.data = RxData()
        self.still_alive = 1
        self.desc = DescID()

    def run(self):
        self.reading_proc()

    def reading_proc(self):
        while self.still_alive:
            d_retval = self.sieca_lib.canRead(self.Canhandle)
            for item in range(0, d_retval["l_len"].value):
                msg1 = d_retval["canmsg"][item]
            s_data = ""
            int_id = self.tabify(self.shortHEX(msg1.l_id, 0), mode=1, tabsize=10)
            for y in range(0, msg1.by_len):
                s_data += self.tabify(self.shortHEX(msg1.aby_data[y], 1))
            flagF, id_n, num = self.data.find(int_id)
            if flagF is False:
                if msg1.l_id != 0:
                    find_flag, sender, reader = self.desc.find(int_id)
                    row = [int_id, s_data, msg1.by_len, 1, sender, reader]
                    self.data.add(row)
                    # запись логов в файл
                    # with open(self.main_path + 'log.txt', 'a') as file:
                    #    file.write("%s\n" % (str(datetime.datetime.now() - self.starttime) + " " + str(row[0]) + " " + row[1] + " " + str(row[2])))
            else:
                self.data.update(num, s_data, msg1.by_len)
                # запись логов в файл
                # with open(self.main_path + 'log.txt', 'a') as file:
                #   file.write("%s\n" % (str(datetime.datetime.now() - self.starttime) + " " + str(int_id) + " " + s_data + " " + str(msg1.by_len)))
        return

    def shortHEX(self, str1, num):
        ret = ""
        buff = str(hex(str1))
        if len(buff[2:]) <= num:
            ret += "0"
            ret += buff[2:]
        else:
            ret += buff[2:]
        return ret

    def tabify(self, s, mode=0,tabsize=4):
        if mode == 0:
            ln = int((len(s) / tabsize) + 1) * tabsize
        else:
            s = s.ljust(tabsize)
            s += "|  "
            return s
        return s.ljust(ln)

    def get_pack(self):
        return self.data.getall()

    def stapth(self):
        self.still_alive = 0

class threadSend(threading.Thread):
    def __init__(self, handle, msg, lib, timeout):
        threading.Thread.__init__(self)
        self.CANhandle = handle
        self.msg = msg
        self.timeout = timeout/1000
        self.sieca_lib = lib
        self.still_alive = 1
    def run(self):
        self.proc()

    def proc(self):
        while self.still_alive:
            result = self.sieca_lib.canSend(self.CANhandle, self.msg, 1)
            if result != 0:
                self.still_alive = 0
            else:
                time.sleep(self.timeout)

    def stapth(self):
        self.still_alive = 0

class DescID:
    def __init__(self):
        self.desc = []
        self.desc.append(["199  |  ", "Джойстики КВГ      |  ", "Контроллер"])
        self.desc.append(["18020203  |  ", "      АЗК          |  ", "Контроллер"])
        self.desc.append(["195  |  ", "ПДУ - дж. движ.    |  ", "Контроллер"])
        self.desc.append(["196  |  ", "ПДУ - дж. навес.   |  ", "Контроллер"])
        self.desc.append(["198  |  ", "ПДУ - об. ДВС      |  ", "Контроллер"])
        self.desc.append(["18050603  |  ", "Датч. пол. отвала  |  ", "Контроллер"])    #Положение отвала
        self.desc.append(["18050703  |  ", "Датч. пол. рамы    |  ", "Контроллер"])    #Положение рамы
        self.desc.append(["18050803  |  ", "Датч. пол. рыхл.   |  ", "Контроллер"])    #Положение рыхл.
        self.desc.append(["18020103  |  ", "   Контроллер      |  ", " Android  "])    #Дж. движения
        self.desc.append(["18020203  |  ", "   Контроллер      |  ", " Android  "])    #Токи насосов, вперед
        self.desc.append(["18020303  |  ", "   Контроллер      |  ", " Android  "])    #Токи насосов, назад
        self.desc.append(["18020403  |  ", "   Контроллер      |  ", " Android  "])    #Токи моторов
        self.desc.append(["18020503  |  ", "   Контроллер      |  ", " Android  "])    #Потенц. ДВС
        self.desc.append(["18020603  |  ", "   Контроллер      |  ", " Android  "])    #Уст. токи насосов
        self.desc.append(["18020703  |  ", "   Контроллер      |  ", " Android  "])    #Уст. токи моторов
        self.desc.append(["18020803  |  ", "   Контроллер      |  ", " Android  "])    #Передача, скорость
        self.desc.append(["18020903  |  ", "   Контроллер      |  ", " Android  "])    #Параметры
        self.desc.append(["18021003  |  ", "   Контроллер      |  ", " Android  "])    #Моточасы, сер.н., токи FAN
        self.desc.append(["18021103  |  ", "   Контроллер      |  ", " Android  "])    #Гран. токов отвала, верт.
        self.desc.append(["18021203  |  ", "   Контроллер      |  ", " Android  "])    #Гран. токов отвала, гориз.
        self.desc.append(["18021303  |  ", "   Контроллер      |  ", " Android  "])    #Гран. токов рыхл., верт.
        self.desc.append(["18021403  |  ", "   Контроллер      |  ", " Android  "])    #Гран. токов рыхл., гориз.
        self.desc.append(["18021503  |  ", "   Контроллер      |  ", " Android  "])    #Давл. насосов, тормоз, плав.
        self.desc.append(["18021603  |  ", "   Контроллер      |  ", " Android  "])    #Давл. насосов навес., FAN
        self.desc.append(["18022003  |  ", "   Контроллер      |  ", "   MI3    "])    #MI3
        self.desc.append(["18022103  |  ", "   Контроллер      |  ", "   MI3    "])    #MI3
        self.desc.append(["18030003  |  ", "    Android        |  ", "Контроллер"])    #параметры
        self.desc.append(["18030303  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030403  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030503  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030603  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030703  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030803  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18030903  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18031003  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18040103  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18040203  |  ", "   Контроллер      |  ", " Дисплей  "])    #
        self.desc.append(["18f00403  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18f00303  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fedf03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["c000003   |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18feee03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fef603  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fef803  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18f00503  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18ff0003  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18f01a03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18feef03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fdd603  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe2003  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe2103  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe6803  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fd9503  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe4703  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18f02103  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fee503  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe2203  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe2303  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe2403  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fe4503  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18f00d03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18febd03  |  ", "     J1939         |  ", "Контроллер"])    #
        self.desc.append(["18fef103  |  ", "     J1939         |  ", "Контроллер"])    #


    def find(self, id_f):
        for i in range(len(self.desc)):
            if self.desc[i][0] == id_f:
                return True, self.desc[i][1], self.desc[i][2]
        return False, "    Unknown        |  ", " Unknown  "



class RxData:
    def __init__(self):
        self.list1 = []

    def add(self, row):
        #index = self.list1.index(row[1])
        #a = str(row[0])
        ret, id_n, ii = self.find(row[0])
        if ret is True:
            self.update(ii, row[1], row[2])
        else:
            self.list1.append(row)

        return row

    def find(self, id_s):
        ret = False
        id_n = 0
        ii = 0
        for i in range(len(self.list1)):
            if self.list1[i][0] == id_s:
                ret = True
                id_n = self.list1[i][0]
                ii = i
                break
        return ret, id_n, ii

    def update(self, num, s_data, s_len):
        self.list1[num][1] = s_data
        self.list1[num][2] = s_len
        self.list1[num][3] = self.list1[num][3] + 1
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
        self.is_connect = 0
        self.counter1 = 0
        self.data = RxData()
        self.desc = DescID()
        self.is_sending = False
        self.is_reading = False
        self.init_window()

    def tabify(self, s, mode=0,tabsize=4):
        if mode == 0:
            ln = int((len(s) / tabsize) + 1) * tabsize
        else:
            s = s.ljust(tabsize)
            s += "|  "
            return s
        return s.ljust(ln)

    def init_window(self):
        defaultMainWindowSizeX = 615
        defaultMainWindowSizeY = 580

        #self.main_path = os.path.dirname(os.path.realpath(__file__))
        self.master.title("CAN Scanner v0.0.1")
        #self.master.maxsize(1020, 60)
        #self.master.minsize(1000, 610)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))

        self.frame1 = tk.Frame(self.master, bd=1, relief=tk.RAISED)
        tkMenu = Menu(self.frame1)
        self.master.config(menu=tkMenu)

        tkMenuConnection = Menu(tkMenu, tearoff=0)
        tkMenuAction = Menu(tkMenu, tearoff=0)
        tkMenu.add_cascade(label="Connection", menu=tkMenuConnection)
        tkMenu.add_cascade(label="Action", menu=tkMenuAction)
        tkMenuConnection.add_command(label="Connect", command=lambda: self.buttonConnectClick())
        tkMenuConnection.add_command(label="Disconnect", command=lambda: self.buttonDisconnectClick())
        tkMenuAction.add_command(label="Read", command=lambda: self.buttonReadClick())
        tkMenuAction.add_command(label="Save log", command=lambda: self.saveLogScript())
        #tkLab = tk.Radiobutton(text='Disconnected', value=0)
        #tkMenu.add_command(label='Disconnected')
        #self.table = Table(self.master, headings=('ID', 'Data', 'Len', 'Count'))
        #self.table.pack(expand=tk.YES, fill=tk.BOTH)
        tkLabel = tk.Label(self.frame1, text='Disconnected')
        tkLabel.pack()
        self.master.bind('<Up>', view_event_up)
        self.master.bind('<Down>', view_event_down)
        self.master.bind('<MouseWheel>', view_event_scroll)

        tabControl = ttk.Notebook(self)
        tabReading = ttk.Frame(tabControl)
        tabDesc = ttk.Frame(tabControl)
        tabSending = ttk.Frame(tabControl)
        tabControl.add(tabReading, text="Reading")
        tabControl.add(tabDesc, text="Description")
        tabControl.add(tabSending, text="Sending")
        #tabControl.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=3, pady=3)
        tabControl.pack(expand=tk.YES, fill=tk.BOTH)
        tabControl.rowconfigure(0, weight=1)
        tabControl.columnconfigure(0, weight=1)
        tabReading.columnconfigure(0, weight=1)
        tabReading.rowconfigure(0, weight=1)
        tabDesc.columnconfigure(0, weight=1)
        tabDesc.rowconfigure(0, weight=1)
        tabSending.columnconfigure(0, weight=1)
        tabSending.rowconfigure(0, weight=1)
        '''self.frameLog = tk.LabelFrame(tabReading, relief=tk.RAISED, borderwidth=1, text="Log")
        self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameLog.columnconfigure(0, weight=20, pad=3)
        self.frameLog.columnconfigure(1, weight=1, pad=3)
        self.frameLog.rowconfigure(0, weight=1, pad=3)'''

        sendFrame = tk.Frame(tabSending)
        sendFrame.grid(row=0, column=0, sticky=tk.W + tk.N + tk.S + tk.E)
        self.textID = tk.Entry(sendFrame, width=8, font='Courier 8')
        self.textID.grid(row=0, column=1, sticky=tk.N + tk.W, columnspan=3, padx=5, pady=5)
        self.textID.bind('<KeyRelease>', self.keyEventID)
        #self.textID.grid(row=2, column=0,row=0, column=1, sticky=tk.N + tk.E, padx=5, pady=5)

        self.textLen = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textLen.grid(row=1, column=1, sticky=tk.N + tk.W, columnspan=3, padx=5, pady=5)
        self.textLen.bind('<KeyRelease>', self.keyEventLen)
        #self.textLen.grid(row=0, column=2, sticky=tk.N + tk.W, padx=5, pady=5)

        self.textData1 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData2 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData3 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData4 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData5 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData6 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData7 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData8 = tk.Entry(sendFrame, width=2, font='Courier 8')
        self.textData1.grid(row=2, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData2.grid(row=2, column=2, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData3.grid(row=2, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData4.grid(row=2, column=4, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData5.grid(row=2, column=5, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData6.grid(row=2, column=6, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData7.grid(row=2, column=7, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData8.grid(row=2, column=8, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textID.insert(tk.INSERT, "18555503")
        self.textData1.insert(tk.INSERT, "00")
        self.textData2.insert(tk.INSERT, "00")
        self.textData3.insert(tk.INSERT, "00")
        self.textData4.insert(tk.INSERT, "00")
        self.textData5.insert(tk.INSERT, "00")
        self.textData6.insert(tk.INSERT, "00")
        self.textData7.insert(tk.INSERT, "00")
        self.textData8.insert(tk.INSERT, "00")
        self.textLen.insert(tk.INSERT, "8")
        self.textData1.bind('<KeyRelease>', self.keyEvent1)
        self.textData2.bind('<KeyRelease>', self.keyEvent2)
        self.textData3.bind('<KeyRelease>', self.keyEvent3)
        self.textData4.bind('<KeyRelease>', self.keyEvent4)
        self.textData5.bind('<KeyRelease>', self.keyEvent5)
        self.textData6.bind('<KeyRelease>', self.keyEvent6)
        self.textData7.bind('<KeyRelease>', self.keyEvent7)
        self.textData8.bind('<KeyRelease>', self.keyEvent8)



        self.textCycle = tk.Entry(sendFrame, width=5, font='Courier 8')
        self.textCycle.grid(columnspan=2, row=3, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textCycle.insert(tk.INSERT, "500")
        self.textCycle.bind('<KeyRelease>', self.keyEventCycle)
        #self.textData.grid(row=0, column=3, sticky=tk.N + tk.W, padx=5, pady=5)


        self.buttonCanSend = tk.Button(sendFrame, wraplength=50, state="normal", text=r"Send", width=10,
                                          command=self.buttonCANSendClick, relief=tk.RAISED)
        self.buttonCanSend.grid(row=4, column=0, columnspan=4, sticky=tk.N + tk.W, padx=5, pady=5)
        #self.buttonCanSend.grid(row=0, column=0, sticky=tk.N + tk.W, padx=5, pady=5)

        self.idLabel = tk.Label(sendFrame, text="ID: ")
        self.lenLabel = tk.Label(sendFrame, text="Len: ")
        self.dataLabel = tk.Label(sendFrame, text="Data: ")
        self.cycleLabel = tk.Label(sendFrame, text="Cycle: ")
        self.idLabel.grid(row=0, column=0, sticky=tk.N + tk.W, padx=5, pady=5)
        self.lenLabel.grid(row=1, column=0, sticky=tk.N + tk.W, padx=5, pady=5)
        self.dataLabel.grid(row=2, column=0, sticky=tk.N + tk.W, padx=5, pady=5)
        self.cycleLabel.grid(row=3, column=0, sticky=tk.N + tk.W, padx=5, pady=5)
        self.resLabel = tk.Label(sendFrame, text="")
        self.resLabel.grid(row=4, column=3, columnspan=5, sticky=tk.N + tk.W, padx=5, pady=5)

        self.listDesc = tk.Listbox(tabDesc, font='Courier')
        self.listDesc.pack(expand=tk.YES, fill=tk.BOTH)
        self.listDesc.bind("<Double-Button-1>", openDescriptionEvent)

        self.flLstResults = tk.Listbox(tabReading, font='Courier')
        #scrollbarF1 = tk.Scrollbar(tabReading, command=self.flLstResults.yview, orient=tk.VERTICAL)
        #self.flLstResults.configure(yscrollcommand=scrollbarF1.set)
        #scrollbarF1.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar = tk.Scrollbar(tabDesc, command=self.listDesc.xview, orient=tk.HORIZONTAL)
        self.listDesc.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.flLstResults.pack(expand=tk.YES, fill=tk.BOTH)


        #self.__add_log_msg__("self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)")
        #buttonConnect = tk.Button(self.master, state="normal", text=r"Connect", command=self.buttonCANConnectClick)
        #buttonConnect.grid()
        #buttonConnect.pack()
        '''label1 = tk.Label(self.master, text="Button: ")
        label1.grid(column=10, row=1)
        label2 = tk.Label(self.master, text="2")
        label2.grid(column=5, row=5)'''
        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.master.mainloop()

    def saveLogScript(self):
        #сохранение логов
        #индикация/сообщение
        return

    def scrollM(self):
        if self.view_p == 0:
            self.yview_listbox = tk.END
        else:
            self.yview_listbox = '0'

    def check_my_msg(self):
        self.counter1 += 1
        w = self.master.geometry()
        if self.counter1 >= 80:
            self.counter1 = 0
            data = self.reading.get_pack()
            self.listDesc.delete(0, tk.END)
            self.flLstResults.delete(0, tk.END)
            self.listDesc.insert(tk.END,
                                u"   ID     |     Отправитель     |   Приемник   | Count")
            self.listDesc.insert(tk.END,
                                 "----------+---------------------+--------------+------")
            self.flLstResults.insert(tk.END, u"   ID     |              Данные              |     | Count")
            self.flLstResults.insert(tk.END, "----------+----------------------------------+-----+------")
            for i in range(0, len(data)):
                self.listDesc.insert(tk.END, str(data[i][0]) + data[i][4] + data[i][5] + "  |  " + str(data[i][3]))
                self.flLstResults.insert(tk.END, str(data[i][0]) + data[i][1] + "|  " + str(data[i][2]) + "  |  " + str(data[i][3]))
            self.listDesc.yview(yview_listbox)
            self.flLstResults.yview(yview_listbox)
        if self.is_connect == 1:
            self.master.after(1, self.check_my_msg)
        else:
            return
        '''d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
        for item in range(0, d_retval["l_len"].value):
            msg1 = d_retval["canmsg"][item]
        # msg2 = d_retval["canmsg"][0]
        s_data = ""
        # s_data = msg1.aby_data
        int_id = self.tabify(self.shortHEX(msg1.l_id, 0), mode=1, tabsize=10)
        for y in range(0, msg1.by_len):
            s_data += self.tabify(self.shortHEX(msg1.aby_data[y], 1))
        #fake_data = self.tabify('11') + self.tabify('22') + self.tabify('33') + self.tabify('44')
        flagF, id_n, num = self.data.find(int_id)
        if flagF is False:
            if msg1.l_id != 0:
        #id_s = self.table.add((hex(msg1.l_id), s_data, " ", d_retval["l_len"].value))
                find_flag, sender, reader = self.desc.find(int_id)
                row = [int_id, s_data, msg1.by_len, 1, sender, reader]
                #if self.master.focus_get() == self.listDesc:
                self.listDesc.insert(tk.END, str(row[0]) + row[4] + "  |  " + row[5] + "|  " + self.tabify("1"))
                self.listDesc.yview(yview_listbox)
                #else:
                self.flLstResults.insert(tk.END, str(row[0]) + row[1] + "|  " + str(row[2])
                                     + "  |  " + self.tabify("1"))
                self.flLstResults.yview(yview_listbox)
                self.data.add(row)
                #запись логов в файл
                #with open(self.main_path + 'log.txt', 'a') as file:
                #    file.write("%s\n" % (str(datetime.datetime.now() - self.starttime) + " " + str(row[0]) + " " + row[1] + " " + str(row[2])))
        else:
            self.data.update(num, s_data, str(msg1.by_len))
            #запись логов в файл
            #with open(self.main_path + 'log.txt', 'a') as file:
            #   file.write("%s\n" % (str(datetime.datetime.now() - self.starttime) + " " + str(int_id) + " " + s_data + " " + str(msg1.by_len)))
            self.counter1 += 1
            w = self.master.geometry()
            if self.counter1 >= 80:
                self.counter1 = 0
                get_row = self.data.getall()
                #if self.master.focus_get() == self.listDesc:
                self.listDesc.delete(0, tk.END)
                self.flLstResults.delete(0, tk.END)
                self.listDesc.insert(tk.END,
                                             u"   ID     |     Отправитель     |   Приемник   | Count")
                self.listDesc.insert(tk.END,
                                             "----------+---------------------+--------------+------")
                self.flLstResults.insert(tk.END, u"   ID     |              Данные              |     | Count")
                self.flLstResults.insert(tk.END, "----------+----------------------------------+-----+------")
                for i in range(0, len(get_row)):
                    self.listDesc.insert(tk.END, str(get_row[i][0]) + get_row[i][4] + get_row[i][5] + "  |  " + str(get_row[i][3]))
                    self.flLstResults.insert(tk.END, str(get_row[i][0]) + get_row[i][1] + "|  " + str(
                        get_row[i][2]) + "  |  " + str(get_row[i][3]))
                    #self.listDesc.insert(tk.END, str(w))
                self.listDesc.yview(yview_listbox)
                #else:
                    #self.flLstResults.delete(0, tk.END)
                    #self.flLstResults.insert(tk.END, u"   ID     |              Данные              |     | Count")
                    #self.flLstResults.insert(tk.END, "----------+----------------------------------+-----+------")
                    #for i in range(0, len(get_row)):
                    #    self.flLstResults.insert(tk.END, str(get_row[i][0]) + get_row[i][1] + "|  " + str(get_row[i][2]) + "  |  " + str(get_row[i][3]))

                    #self.flLstResults.insert(tk.END, str(w))
                self.flLstResults.yview(yview_listbox)
                #self.
                #self.flLstResults.()
            #self.table.update(id_n, (get_row[1], get_row[2], get_row[3], get_row[4]))


        #self.flLstResults.delete(0, tk.END)
        if self.is_connect == 1:
            self.master.after(1, self.check_my_msg)
        else:
            return'''

    def shortHEX(self, str1, num):
        ret = ""
        buff = str(hex(str1))
        if len(buff[2:]) <= num:
            ret += "0"
            ret += buff[2:]
        else:
            ret += buff[2:]
        return ret

    def buttonReadClick(self):
        if self.is_connect == 1:
            self.starttime = datetime.datetime.now()
            self.reading = threadRead(self.siecaLibHandle, self.sieca_lib)
            self.reading.start()
            self.is_reading = self.reading.is_alive()
            if self.is_reading is True:
                self.check_my_msg()
        else:
            pass
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
        if d_retval["l_retval"] == 0:
            self.is_connect = 1
            self.siecaLibHandle = d_retval["handle"]
            l_retval = self.sieca_lib.canSetBaudrate(self.siecaLibHandle,
                                                    int(CANTypeDefs.Baudrate.BAUD_250))  # 250 kbits/sec
            if l_retval == 0:
                l_retval = self.sieca_lib.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
                if l_retval == 0:
                    l_retval = self.sieca_lib.canIsNetOwner(d_retval["handle"])
                    if l_retval == 0:
                        l_retval = self.sieca_lib.canSetFilterMode(self.siecaLibHandle, CANTypeDefs.T_FILTER_MODE.filterMode_nofilter)
                        if l_retval == 0:
                            global view_p
                            view_p = 0
        else:
            #message
            pass
        return

    def buttonCANSendClick(self):
        id_m = int(self.textID.get(), 16)
        len_m = int(self.textLen.get())
        data1 = int(self.textData1.get(), 16)
        data2 = int(self.textData2.get(), 16)
        data3 = int(self.textData3.get(), 16)
        data4 = int(self.textData4.get(), 16)
        data5 = int(self.textData5.get(), 16)
        data6 = int(self.textData6.get(), 16)
        data7 = int(self.textData7.get(), 16)
        data8 = int(self.textData8.get(), 16)
        cycle_m = int(self.textCycle.get())
        canmsg = CANTypeDefs.CMSG()
        canmsg.l_id = id_m
        canmsg.by_len = len_m
        bytedata = bytearray([data1, data2, data3, data4, data5, data6, data7, data8])
        canmsg.aby_data[:] = bytedata
        canmsg.by_extended = 1
        canmsg.by_remote = 0
        if self.is_sending is False:
            self.sending = threadSend(self.siecaLibHandle, canmsg, self.sieca_lib, cycle_m)
            self.sending.start()
            self.is_sending = self.sending.is_alive()
            if self.is_sending is True:
                self.buttonCanSend.configure(text=r"Stop", relief=tk.SUNKEN)
        else:
            self.sending.stapth()
            self.sending.join()
            self.is_sending = self.sending.is_alive()
            if self.is_sending is False:
                self.buttonCanSend.configure(text=r"Send", relief=tk.RAISED)
        return


    def buttonDisconnectClick(self):
        if self.is_connect == 1:
            if self.is_reading is True:
                self.reading.stapth()
                self.reading.join()
                self.is_reading = self.reading.is_alive()
                if self.is_reading is False:
                    l_retval = self.sieca_lib.canClose(self.siecaLibHandle)
                    if l_retval == 0:
                        self.is_connect = 0
                        global view_p
                        view_p = 2
        #self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(l_retval))
        #self.flLstResults.delete(0, tk.END)
        return

    def keyEvent1(self, event):
        if len(self.textData1.get()) > 2:
            self.textData1.delete(0, tk.END)

    def keyEvent2(self, event):
        if len(self.textData2.get()) > 2:
            self.textData2.delete(0, tk.END)

    def keyEvent3(self, event):
        if len(self.textData3.get()) > 2:
            self.textData3.delete(0, tk.END)

    def keyEvent4(self, event):
        if len(self.textData4.get()) > 2:
            self.textData4.delete(0, tk.END)

    def keyEvent5(self, event):
        if len(self.textData5.get()) > 2:
            self.textData5.delete(0, tk.END)

    def keyEvent6(self, event):
        if len(self.textData6.get()) > 2:
            self.textData6.delete(0, tk.END)

    def keyEvent7(self, event):
        if len(self.textData7.get()) > 2:
            self.textData7.delete(0, tk.END)

    def keyEvent8(self, event):
        if len(self.textData8.get()) > 2:
            self.textData8.delete(0, tk.END)

    def keyEventID(self, event):
        if len(self.textID.get()) > 8:
            self.textID.delete(0, tk.END)

    def keyEventLen(self, event):
        if len(self.textLen.get()) > 1:
            self.textLen.delete(0, tk.END)

    def keyEventCycle(self, event):
        if len(self.textCycle.get()) > 5:
            self.textCycle.delete(0, tk.END)

def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()