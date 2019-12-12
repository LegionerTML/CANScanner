import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import datetime
import platform
import CANTypeDefs
import tkinter.ttk as ttk

#if platform.architecture()[0] == '32bit':
from sieca132_client_x32 import sieca132_client
#else:
#   from sieca132_client_x64 import sieca132_client

view_p = 2
yview_listbox = '0'

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
        self.init_window()
        self.id1 = []


    def __add_log_msg__(self, message):
        self.flLstResults.insert(tk.END, "[" + datetime.datetime.now().strftime("%H:%M:%S")+"] " + message)
        self.flLstResults.yview(tk.END)
        return

    def tabify(self, s, mode=0,tabsize=4):
        if mode == 0:
            ln = int((len(s) / tabsize) + 1) * tabsize
        else:
            s = s.ljust(tabsize)
            s += "|  "
            return s
        return s.ljust(ln)

    def init_window(self):
        defaultMainWindowSizeX = 1080
        defaultMainWindowSizeY = 620


        self.master.title("CAN Scanner v0.0.1")
        #self.master.maxsize(1020, 60)
        self.master.minsize(1000, 610)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))

        tkMenu = Menu(self.master)
        self.master.config(menu=tkMenu)

        tkMenuItemFile = Menu(tkMenu, tearoff=0)
        tkMenu.add_cascade(label="Program", menu=tkMenuItemFile)
        tkMenuItemFile.add_command(label="Connect", command=lambda: self.buttonConnectClick())
        #tkMenuItemFile.add_command(label="Add", command=lambda: self.buttonAddClick())
        tkMenuItemFile.add_command(label="Disconnect", command=lambda: self.buttonDisconnectClick())
        #self.table = Table(self.master, headings=('ID', 'Data', 'Len', 'Count'))
        #self.table.pack(expand=tk.YES, fill=tk.BOTH)

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

        self.textID = tk.Text(tabSending, height=1,width=10,font='Courier',wrap=tk.WORD)
        self.textID.grid(row=0, column=1, sticky=tk.N + tk.E, padx=5, pady=5)

        self.textLen = tk.Text(tabSending, height=1, width=5, font='Courier', wrap=tk.WORD)
        self.textLen.grid(row=0, column=2, sticky=tk.N + tk.W, padx=5, pady=5)

        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=0, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        '''self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=1, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=2, column=3, sticky=tk.N + tk.W, padx=5, pady=5)'''
        '''self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=3, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=4, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=5, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=6, column=3, sticky=tk.N + tk.W, padx=5, pady=5)
        self.textData = tk.Text(tabSending, height=1, width=10, font='Courier', wrap=tk.WORD)
        self.textData.grid(row=7, column=3, sticky=tk.N + tk.W, padx=5, pady=5)'''

        self.buttonCanSend = tk.Button(tabSending, wraplength=50, state="normal", text=r"Send",
                                          command=self.buttonCANSendClick)
        self.buttonCanSend.grid(row=0, column=0, sticky=tk.N + tk.W, padx=5, pady=5)

        self.flLstResults = tk.Listbox(tabReading, font = 'Courier')
        #scrollbar = tk.Scrollbar(self, command=self.flLstResults.yview)
        #self.flLstResults.configure(yscrollcommand=scrollbar.set)
        #scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        #self.flLstResults.config(height=20)
        #self.flLstResults.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.flLstResults.pack(expand=tk.YES, fill=tk.BOTH)

        self.listDesc = tk.Listbox(tabDesc, font='Courier')
        self.listDesc.pack(expand=tk.YES, fill=tk.BOTH)
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

    def scrollM(self):
        if self.view_p == 0:
            self.yview_listbox = tk.END
        else:
            self.yview_listbox = '0'

    def check_my_msg(self):
        #i = 0
        #while i<30:
        d_retval = self.sieca_lib.canRead(self.siecaLibHandle)

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
                self.__add_log_msg__(str(row[0]) + row[4] + "  |  " + row[5] + "|  " + row[1] + "|  " + str(row[2])
                                     + "  |  " + self.tabify("1")) #str(msg1.by_len) + " " +
                self.data.add(row)
        else:
            self.data.update(num, s_data, str(msg1.by_len))
            self.counter1 += 1
            if self.counter1 >= 80:
                self.counter1 = 0
                get_row = self.data.getall()
                self.flLstResults.delete(0, tk.END)

                self.flLstResults.insert(tk.END, u"              ID     |     Отправитель     |   Приемник   |              Данные              |     | Count")
                self.flLstResults.insert(tk.END, "---------------------+---------------------+--------------+----------------------------------+-----+------")
                for i in range(0, len(get_row)):
                    self.__add_log_msg__(str(get_row[i][0]) + get_row[i][4] + get_row[i][5] + "  |  "
                                         + get_row[i][1] + "|  " + str(get_row[i][2]) + "  |  " + str(get_row[i][3]))
                self.flLstResults.yview(yview_listbox)

                #self.flLstResults.()
            #self.table.update(id_n, (get_row[1], get_row[2], get_row[3], get_row[4]))


        #self.flLstResults.delete(0, tk.END)

        '''list_s = self.data.getall()
        for i in range(len(list_s)):
            self.__add_log_msg__(str(list_s[i]))'''
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
                            self.check_my_msg()
        else:
            #message
            pass
        # siecaDllInfo = CANTypeDefs.st_InternalDLLInformation()
        # res = self.sieca_lib.canGetDllInfo(ctypes.addressof(siecaDllInfo))
        #self.flLstResults.insert(tk.END, "sieca_lib: " + str(self.sieca_lib))
        # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(res))
        # self.flLstResults.insert(tk.END, siecaDllInfo.aui_TxCounter)
        #self.flLstResults.insert(tk.END, "Set Baudrate: " + str(CANTypeDefs.ReturnValues(l_retval)))
        #self.flLstResults.insert(tk.END, "LED flashing settings applied: " + str(CANTypeDefs.ReturnValues(l_retval)))
        #self.flLstResults.insert(tk.END, "CanIsNetOwner: " + str(CANTypeDefs.ReturnValues(l_retval)))
        #self.flLstResults.insert(tk.END, "CanSetFilterMode: " + str(CANTypeDefs.ReturnValues(l_retval)))
        #message_reader = ThreadCANMsgReader(self.siecaLibHandle, self.sieca_lib, self.QueueIncomingMessages)
        #message_reader.start()
        # d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
        # self.flLstResults.insert(tk.END, "DataCount: " + str(d_retval["l_len"]))
        # self.flLstResults.insert(tk.END, "DataCount: " + str(CANTypeDefs.ReturnValues(d_retval["l_retval"])))
        '''d_retval = self.sieca_lib.canRead(self.canfox_handle)
        for item in range(0, d_retval["l_len"].value):
            self.queue.put(d_retval["canmsg"][item])
        i = 0
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

    def buttonCANSendClick(self):
        mess = []
        mess.append(0x18555503)
        mess.append(8)
        mess.append([0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15])
        mess.append(1)
        mess.append(0)
        self.SendMsg(mess)
        return

    def SendMsg(self, msg, timeout=None):
        canmsg = CANTypeDefs.CMSG()
        canmsg.l_id = msg[0]
        canmsg.by_len = msg[1]
        bytedata = bytearray(msg[2])
        canmsg.aby_data[:] = bytedata
        canmsg.by_extended = msg[3]
        canmsg.by_remote = msg[4]

        '''result = self.sieca_client.canSend(self.siecaLibHandle, canmsg, 1)
        if result == 0:
            #goodmessage
            pass
        else:
            #badmessage
            pass'''
        return

    def buttonDisconnectClick(self):
        if self.is_connect == 1:
            l_retval = self.sieca_lib.canClose(self.siecaLibHandle)
            if l_retval == 0:
                self.is_connect = 0
                global view_p
                view_p = 2
        #self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(l_retval))
        #self.flLstResults.delete(0, tk.END)
        return

def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()