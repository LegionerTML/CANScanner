import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import datetime
import CANTypeDefs
import tkinter.ttk as ttk
import os
import threading
import time

from sieca132_client_x32 import sieca132_client

view_p = 2
yview_listbox = '0'




def openDescriptionEvent(event):
    pass
    #root = tk.Tk()
    #app1 = DescApplication(root)

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
    def __init__(self, handle, lib, time):
        threading.Thread.__init__(self)
        self.Canhandle = handle
        self.sieca_lib = lib
        self.data = RxData()
        self.still_alive = 1
        self.is_logging = False
        self.desc = DescID()
        self.start_time = time
        self.main_path = os.path.dirname(os.path.realpath(__file__))
        self.file = 0
        with open(self.main_path + '/log.txt', 'w'):
            pass

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
            if self.is_logging is True:
                try:
                    self.file.write("%s\n" % (str(datetime.datetime.now() - self.start_time) + " " + int_id + " " +
                                    s_data + " " + str(msg1.by_len)))
                except Exception:
                    self.file = open(self.main_path + '/log.txt', 'a')
            if flagF is False:
                if msg1.l_id != 0:
                    find_flag, sender, reader = self.desc.find(int_id)
                    row = [int_id, s_data, msg1.by_len, 1, sender, reader]
                    self.data.add(row)
            else:
                self.data.update(num, s_data, msg1.by_len)
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

    def reset(self):
        self.data.clear()

    def get_pack(self):
        return self.data.getall()

    def get_log(self, state):
        self.is_logging = state
        if self.is_logging is True:
            self.file = open(self.main_path + '/log.txt', 'a')
        else:
            self.file.close()

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

class DescApplication(tk.Frame):
    def __init__(self, master = None):
        self.master = master
        tk.Frame.__init__(self, master)
        self.init_window()

    def init_window(self):
        defaultMainWindowSizeX = 615
        defaultMainWindowSizeY = 580

        self.master.title("CAN Scanner v1.0")
        self.master.maxsize(615, 580)
        self.master.minsize(615, 580)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))
        mainframe = tk.Frame(self, bd=1, relief=tk.RAISED)
        mainframe.pack(expand=tk.YES, fill=tk.BOTH)

        self.textData1 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData2 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData3 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData4 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData5 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData6 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData7 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData8 = tk.Entry(mainframe, width=2, font='Courier 8')
        self.textData1.grid(row=2, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData2.grid(row=3, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData3.grid(row=4, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData4.grid(row=5, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData5.grid(row=6, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData6.grid(row=7, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData7.grid(row=8, column=1, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData8.grid(row=9, column=1, sticky=tk.N + tk.W, padx=5, pady=5)


        self.idLabel = tk.Label(mainframe, text="ID: ")
        self.dataLabel = tk.Label(mainframe, text="Data: ")

        self.idLabel.grid(row=0, column=0, sticky=tk.N + tk.W, padx=5, pady=5)

        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.master.mainloop()

class MainApplication(tk.Frame):
    def __init__(self, master = None):
        self.master = master
        tk.Frame.__init__(self, master)
        self.is_connect = 0
        self.counter1 = 0
        self.data = RxData()
        self.desc = DescID()
        self.counter_sel_all = 0
        self.is_sel_all = tk.BooleanVar()
        self.is_sel_all.set(0)
        self.solomess = [tk.BooleanVar() for i in range(10)]
        for i in range(10):
            self.solomess[i].set(0)

        self.solomessOnce = tk.BooleanVar()
        self.solomessOnce.set(0)
        self.is_sending = False
        self.is_reading = False
        self.is_logging = False
        self.init_window()

    def tabify(self, s, mode=0,tabsize=4):
        if mode == 0:
            ln = int((len(s) / tabsize) + 1) * tabsize
        else:
            s = s.ljust(tabsize)
            s += "|  "
            return s
        return s.ljust(ln)

    def test(self):
        self.sendList.insert(tk.END, str(self.solomess.get()))

    def select_all(self):
        if self.is_sel_all.get() == 1:
            for i in range(10):
                self.checkbtnSendArr[i].select()
        else:
            for i in range(10):
                self.checkbtnSendArr[i].deselect()

    def init_window(self):
        defaultMainWindowSizeX = 615
        defaultMainWindowSizeY = 580

        self.master.title("CAN Scanner v0.0.1")
        self.master.maxsize(615, 580)
        self.master.minsize(615, 580)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))

        self.frame1 = tk.Frame(self.master, bd=1, relief=tk.RAISED)
        self.tkMenu = Menu(self.frame1)
        self.master.config(menu=self.tkMenu)

        self.tkMenuConnection = Menu(self.tkMenu, tearoff=0)
        self.tkMenuAction = Menu(self.tkMenu, tearoff=0)
        self.tkMenu.add_cascade(label="Connection", menu=self.tkMenuConnection)
        self.tkMenuConnection.add_command(label="Connect", command=lambda: self.buttonConnectionClick())
        self.tkMenu.add_cascade(label="Action", menu=self.tkMenuAction)
        self.tkMenuAction.add_command(label="Read", command=lambda: self.buttonReadClick())
        self.tkMenuAction.add_command(label="Save log", command=lambda: self.saveLogScript())
        self.tkMenuAction.add_command(label="Reset", command=lambda: self.buttonReset())
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
        tabControl.pack(expand=tk.YES, fill=tk.BOTH)
        tabControl.rowconfigure(0, weight=1)
        tabControl.columnconfigure(0, weight=1)
        tabReading.columnconfigure(0, weight=1)
        tabReading.rowconfigure(0, weight=1)
        tabDesc.columnconfigure(0, weight=1)
        tabDesc.rowconfigure(0, weight=1)
        tabSending.columnconfigure(0, weight=1)
        tabSending.rowconfigure(0, weight=1)

        sendFrame = tk.Frame(tabSending)
        sendFrameLB = tk.Frame(tabSending)
        sendFrame.pack(expand=tk.YES, fill=tk.X)
        sendFrameLB.pack(expand=tk.YES, fill=tk.BOTH)
        self.sendList = tk.Listbox(sendFrameLB, font='Courier 10')
        self.sendList.pack(expand=tk.YES, fill=tk.BOTH)
        self.textIDArr = [tk.Entry(sendFrame, width=8, font='Courier 8') for i in range(10)]
        self.textDataArr = [[tk.Entry(sendFrame, width=2, font='Courier 8') for j in range(8)] for i in range(10)]
        self.textCycleArr = [tk.Entry(sendFrame, width=5, font='Courier 8') for i in range(10)]
        self.checkbtnSendArr = [tk.Checkbutton(sendFrame, text="Send", onvalue=1, offvalue=0, variable=self.solomess[i], state="normal", width=10) for i in range(10)]
        self.idLabelArr = [tk.Label(sendFrame, text="ID: ") for i in range(10)]
        self.dataLabelArr = [tk.Label(sendFrame, text="Data: ") for i in range(10)]
        self.cycleLabelArr = [tk.Label(sendFrame, text="Cycle (ms): ") for i in range(10)]
        for i in range(10):
            self.textIDArr[i].grid(row=i, column=5, sticky=tk.N + tk.W, columnspan=3, padx=5, pady=5)
            strID = ""
            strID += "10" + str(i) + "00" + str(i) + "03"
            self.textIDArr[i].insert(tk.INSERT, strID)
            self.textIDArr[i].bind('<KeyRelease>', self.keyEventID)
            for j in range(8):
                self.textDataArr[i][j].grid(row=i, column=(j+9), sticky=tk.N + tk.W, padx=5, pady=5)
                self.textDataArr[i][j].insert(tk.INSERT, "00")
                self.textDataArr[i][j].bind('<KeyRelease>', self.keyEvent)
            self.textCycleArr[i].grid(row=i, column=18, columnspan=2, sticky=tk.N + tk.W, padx=5, pady=5)
            self.textCycleArr[i].insert(tk.INSERT, "500")
            self.textCycleArr[i].bind('<KeyRelease>', self.keyEventCycle)
            self.checkbtnSendArr[i].grid(row=i, column=0, columnspan=4, sticky=tk.N + tk.W, padx=0, pady=2)
            #self.checkbtnSendArr[i].bind('<ButtonRelease-1>', self.check_click)
            self.idLabelArr[i].grid(row=i, column=4, sticky=tk.N + tk.W, padx=0, pady=4)
            self.dataLabelArr[i].grid(row=i, column=8, sticky=tk.N + tk.W, padx=0, pady=4)
            self.cycleLabelArr[i].grid(row=i, column=17, sticky=tk.N + tk.W, padx=0, pady=4)

        self.checkbtnSelAll = tk.Checkbutton(sendFrame, text="Select all", onvalue=1, offvalue=0, variable=self.is_sel_all, command=self.select_all, state="normal", width=10)
        self.checkbtnSelAll.grid(row=12, column=0, columnspan=4, sticky=tk.N + tk.W, padx=0, pady=2)

        self.buttonCanSend = tk.Button(sendFrame, wraplength=50, state="normal", text=r"Send", width=10,
                                          command=self.buttonCANSendClick, relief=tk.RAISED)
        self.buttonCanSend.grid(row=11, column=0, columnspan=4, sticky=tk.N + tk.W, padx=5, pady=5)
        self.checkbtnCanSendOnce = tk.Checkbutton(sendFrame, text="Send once", onvalue=1, offvalue=0,
                                              variable=self.solomessOnce, state="normal", width=10)
        self.checkbtnCanSendOnce.grid(row=11, column=4, columnspan=4, sticky=tk.N + tk.W, padx=0, pady=5)




        self.resLabel = tk.Label(sendFrame, text="")
        self.resLabel.grid(row=11, column=8, columnspan=5, sticky=tk.N + tk.W, padx=5, pady=5)

        self.listDesc = tk.Listbox(tabDesc, font='Courier')
        self.listDesc.pack(expand=tk.YES, fill=tk.BOTH)
        #self.listDesc.bind("<Double-Button-1>", openDescriptionEvent)

        self.flLstResults = tk.Listbox(tabReading, font='Courier')
        scrollbar = tk.Scrollbar(tabDesc, command=self.listDesc.xview, orient=tk.HORIZONTAL)
        self.listDesc.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.flLstResults.pack(expand=tk.YES, fill=tk.BOTH)
        #self.flLstResults.bind("<Double-Button-1>", openDescriptionEvent)

        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.master.mainloop()

    def saveLogScript(self):
        if self.is_logging is False and self.is_reading is True:
            self.is_logging = True
            self.reading.get_log(self.is_logging)
            self.tkMenuAction.entryconfig(1, label="Stop saving log")
        else:
            self.is_logging = False
            self.reading.get_log(self.is_logging)
            self.tkMenuAction.entryconfig(1, label="Save log")

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
            if self.is_reading is False:
                self.starttime = datetime.datetime.now()
                self.reading = threadRead(self.siecaLibHandle, self.sieca_lib, self.starttime)
                self.reading.start()
                self.is_reading = self.reading.is_alive()
                if self.is_reading is True:
                    self.check_my_msg()
        return

    def buttonReset(self):
        if self.is_connect == 1:
            if self.is_reading is True:
                self.reading.reset()

    def buttonConnectionClick(self):
        if self.is_connect == 0:
            self.buttonConnectClick()
        else:
            self.buttonDisconnectClick()

    def buttonConnectClick(self):
        if self.is_connect == 0:
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
                                self.tkMenuConnection.entryconfig(0, label="Disconnect")
                                #self.tkMenu.entryconfig(0, label="Disconnect")
            else:
                #message
                pass
        else:
            pass

    def getData(self):
        all_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        all_cycles = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        all_is_clear = 0

        for i in range(10):
            if self.solomess[i].get() is True:
                cycle_m = int(self.textCycleArr[i].get())
                canmsg = CANTypeDefs.CMSG()
                canmsg.l_id = int(self.textIDArr[i].get(), 16)
                canmsg.by_len = 8
                bytedata = bytearray(
                    [int(self.textDataArr[i][0].get(), 16), int(self.textDataArr[i][1].get(), 16), int(self.textDataArr[i][2].get(), 16),
                     int(self.textDataArr[i][3].get(), 16), int(self.textDataArr[i][4].get(), 16), int(self.textDataArr[i][5].get(), 16),
                     int(self.textDataArr[i][6].get(), 16), int(self.textDataArr[i][7].get(), 16)])
                canmsg.aby_data[:] = bytedata
                canmsg.by_extended = 1
                canmsg.by_remote = 0
                all_cycles[i] = cycle_m
                all_data[i] = canmsg
            else:
                all_cycles[i] = 0
                all_data[i] = 0
                all_is_clear += 1

        return all_data, 10-all_is_clear, all_cycles

    def buttonCANSendClick(self):
        if self.is_sending is False and self.is_connect == 1:
            self.sendList.delete(0, tk.END)
            all_msgs, self.count_msg, all_cycles = self.getData()
            if self.count_msg == 0:
                self.sendList.insert(tk.END, "Nothing selected!")
            else:
                if self.solomessOnce.get() is True:
                    for i in range(10):
                        if self.solomess[i].get() is True:
                            result = self.sieca_lib.canSend(self.siecaLibHandle, all_msgs[i], 1)
                            if result == 0:
                                strMsg = ""
                                strMsg += "Message " + str(i+1) + " sent."
                                self.sendList.insert(tk.END, strMsg)

                else:
                    counter = 0
                    self.sending = []
                    for i in range(10):
                        if self.solomess[i].get() is True:
                            self.sending.append(threadSend(self.siecaLibHandle, all_msgs[i], self.sieca_lib, all_cycles[i]))
                            self.sending[counter].start()
                            if self.sending[counter].is_alive():
                                counter += 1
                            strMsg = ""
                            strMsg += "Message is sending."
                            self.sendList.insert(tk.END, strMsg)
                    if counter == self.count_msg:
                        self.is_sending = True
                        self.buttonCanSend.configure(text=r"Stop", relief=tk.SUNKEN)
                        for i in range(10):
                            self.checkbtnSendArr[i].configure(state=tk.DISABLED)
                        self.checkbtnCanSendOnce.configure(state=tk.DISABLED)

        else:
            if self.is_sending is True:
                counter = 0
                for i in range(self.count_msg):
                    self.sending[i].stapth()
                    self.sending[i].join()
                    if self.sending[i].is_alive() is False:
                        counter += 1
                if counter == self.count_msg:
                    for i in range(10):
                        self.checkbtnSendArr[i].configure(state=tk.NORMAL)
                    self.checkbtnCanSendOnce.configure(state=tk.NORMAL)
                    self.buttonCanSend.configure(text=r"Send", relief=tk.RAISED)
                    self.sendList.insert(tk.END, "Sending was stopped")
                    self.is_sending = False
            else:
                self.sendList.insert(tk.END, "Connection was not found")
        return


    def buttonDisconnectClick(self):
        if self.is_connect == 1:
            if self.is_reading is True:
                self.reading.stapth()
                self.reading.join()
                self.is_reading = self.reading.is_alive()
                if self.is_reading is True:
                    return
            if self.is_sending is True:
                counter = 0
                for i in range(self.count_msg):
                    self.sending[i].stapth()
                    self.sending[i].join()
                    if self.sending[i].is_alive() is False:
                        counter += 1
                if counter == self.count_msg:
                    self.is_sending = False
                    self.checkbtnCanSendOnce.configure(state=tk.NORMAL)
                    self.buttonCanSend.configure(text=r"Send", relief=tk.RAISED)
                    self.sendList.insert(tk.END, "Sending was stopped")
                    for i in range(10):
                        self.checkbtnSendArr[i].configure(state=tk.NORMAL)
                else:
                    return
            l_retval = self.sieca_lib.canClose(self.siecaLibHandle)
            if l_retval == 0:
                self.is_connect = 0
                global view_p
                view_p = 2
                self.tkMenuConnection.entryconfig(0, label="Connect")
        return

    def keyEvent(self, event):
        if len(event.widget.get()) > 2:
            event.widget.delete(0, tk.END)

    def keyEventID(self, event):
        if len(event.widget.get()) > 8:
            event.widget.delete(0, tk.END)

    def keyEventCycle(self, event):
        if len(event.widget.get()) > 5:
            event.widget.delete(0, tk.END)

    def check_click(self, event):
        counter_sel_all1 = 0
        for i in range(10):
            if self.solomess[i].get() is True:
                counter_sel_all1 += 1
        if counter_sel_all1 == 10:
            self.checkbtnSelAll.select()
        else:
            self.checkbtnSelAll.deselect()

def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()