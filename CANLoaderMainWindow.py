import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import datetime
from threading import Thread
import os
from ctypes import *
from CANLoaderController import CANLoaderController, CANLoaderFirmwareVerifyException, CANLoaderDeviceFailureException
import queue
from CANFoxLib import CANFoxLibSkin, CANfoxException, CANfoxHardwareException
from enum import *
import settings
import platform
import CANTypeDefs
from ThreadCANMsgReader import ThreadCANMsgReader

if platform.architecture()[0] == '32bit':
    from sieca132_client_x32 import sieca132_client
else:
    from sieca132_client_x64 import sieca132_client

import CANLoaderAbout


class te_OperationState(Enum):
    os_BEGIN = 0
    os_END = 1

    def __int__(self):
        return self.value


class WorkingAction(Enum):
    wa_INIT = 0
    wa_NONE = 1
    wa_PROGRAMMING = 2
    wa_VERIFYING = 3
    wa_DEVICE_READING = 4
    wa_ERROR = 5
    wa_HARDWARE_ERROR = 6

    def __int__(self):
        return self.value

class te_CurrentDeviceBootloaderState(Enum):
    bs_InBootloader = 0
    bs_Unknown = 1

    def __int__(self):
        return self.value


class MainApplication(tk.Frame):
    def __init__(self, master=None):
        self.master = master
        tk.Frame.__init__(self, master)
        self.QueueProgressBar = queue.Queue(10)
        self.QueueThreadProgrammingService = queue.Queue(1)
        self.QueueThreadVerifyingService = queue.Queue(1)
        self.QueueThreadReadingService = queue.Queue(1)
        self.QueueIncomingMessages = queue.Queue(100)
        self.__can_hasReprogrammableDevices = False
        self.__workingAction = WorkingAction.wa_NONE
        self.init_window()

    def key(self, event):
        kp = event.char
        esc_key = chr(0x1b)
        if kp == esc_key:
            {
                WorkingAction.wa_NONE: lambda: None,
                WorkingAction.wa_PROGRAMMING: lambda: self.QueueThreadProgrammingService.put("exit") if (messagebox.askyesno("Cancel programming?")) else None,
                WorkingAction.wa_VERIFYING: lambda: self.QueueThreadVerifyingService.put("exit") if (messagebox.askyesno("Cancel verifying?")) else None,
                WorkingAction.wa_DEVICE_READING: lambda: self.QueueThreadReadingService.put("exit") if (messagebox.askyesno("Cancel reading?")) else None,
                WorkingAction.wa_ERROR: lambda: None,
                WorkingAction.wa_HARDWARE_ERROR: lambda: None

            }[self.__workingAction]()

    def __enable_find_controls__(self):
        self.__enable_controls__(self.frameCanDevice)
        self.buttonLeaveBootloader.configure(state='disable')
        self.buttonLock.configure(state='disable')
        self.buttonCanConnect.configure(state='disable')
        return

    def __disable_controls__(self, parent):
        for child in parent.winfo_children():
            try:
                child.configure(state='disable')
            except Exception as e:
                continue
        return

    def __enable_controls__(self, parent):
        for child in parent.winfo_children():
            try:
                child.configure(state='normal')
            except Exception as e:
                continue
        return

    def __enable_controls_programming__(self):
        if hasattr(self, 'reprogrammable_devices') and len(self.reprogrammable_devices) != 0:
            if os.path.exists(self.flashFilePath.get()) and os.path.getsize(str(self.flashFilePath.get())) > 0:
                self.__enable_controls__(self.frameProgramming)
                self.entryFlashFile.configure(state="disable")
            if hasattr(self, 'CurrentDeviceBootloaderState') and self.CurrentDeviceBootloaderState == te_CurrentDeviceBootloaderState.bs_InBootloader:
                self.buttonLeaveBootloader.configure(state="normal")
                self.buttonLock.configure(state="normal")
            else:
                self.buttonLeaveBootloader.configure(state="disable")
                self.buttonLock.configure(state="disable")
            self.buttonReadFlash.configure(state='normal')
            self.buttonSelectFlashFile.configure(state='normal')
        else:
            self.labelStatus['text'] = "None"
            self.labelStatus.config(bg="gray")
            self.entryNodeIDText.set("")
            self.entryMCUInfoText.set("")
            self.__disable_controls_programming__()
        return

    def __disable_controls_programming__(self):
        self.__disable_controls__(self.frameProgramming)
        self.buttonLeaveBootloader.configure(state="disable")
        self.buttonLock.configure(state="disable")
        return

    def __enable_controls_device__(self):
        self.__enable_controls__(self.frameFoundCanDevices)
        self.__enable_controls__(self.frameCanDevice)
        self.comboboxFoundCanDevices.configure(state="readonly")
        self.buttonCanConnect.config(state="disabled")
        return

    def __disable_controls_device__(self):
        self.__disable_controls__(self.frameCanDevice)
        self.__disable_controls__(self.frameFoundCanDevices)
        self.buttonFind.config(state="disabled")
        return

    def __reset_all_controls__(self):
        self.__disable_controls__(self.frameCanDevice)
        self.__disable_controls__(self.frameFoundCanDevices)
        self.buttonFind.config(state="normal")
        self.buttonCanConnect.config(state="normal")

    def __switch_controls__(self, operation_state):
        if operation_state == te_OperationState.os_BEGIN:
            {
                WorkingAction.wa_INIT: lambda: self.__reset_all_controls__(),
                WorkingAction.wa_NONE: lambda: self.__disable_controls_programming__(),
                WorkingAction.wa_PROGRAMMING: lambda: (self.__disable_controls_programming__(), self.__disable_controls_device__()),
                WorkingAction.wa_VERIFYING: lambda: (self.__disable_controls_programming__(), self.__disable_controls_device__()),
                WorkingAction.wa_DEVICE_READING: lambda: (self.__disable_controls_programming__(), self.__disable_controls_device__()),
                WorkingAction.wa_ERROR: lambda: (self.__disable_controls_programming__(), self.__disable_controls_device__()),
                WorkingAction.wa_HARDWARE_ERROR: lambda: (self.__reset_all_controls__())
            }[self.__workingAction]()
        else:
            {
                WorkingAction.wa_INIT: lambda: self.__reset_all_controls__(),
                WorkingAction.wa_NONE: lambda: (self.__enable_controls_device__(), self.__enable_controls_programming__()),
                WorkingAction.wa_PROGRAMMING: lambda: None,
                WorkingAction.wa_VERIFYING: lambda: None,
                WorkingAction.wa_DEVICE_READING: lambda: None,
                WorkingAction.wa_ERROR: lambda: (self.__disable_controls_programming__(), self.__disable_controls_device__(), self.__enable_find_controls__()),
                WorkingAction.wa_HARDWARE_ERROR: lambda: (self.__reset_all_controls__())
            }[self.__workingAction]()
        return
    def __add_log_msg__(self, message):
        self.flLstResults.insert(tk.END, "[" + datetime.datetime.now().strftime("%H:%M:%S")+"] " + message)
        self.flLstResults.yview(tk.END)
        return


    # Creation of init_window
    def init_window(self):
        defaultMainWindowSizeX = 600
        defaultMainWindowSizeY = 400
        # changing the title of our master widget
        t = os.path.getmtime(os.path.realpath(__file__))
        self.master.title("CAN Update Manager v1.002." + str(int(t))+"b")
        self.master.minsize(100, 100)
        self.master.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))
        self.master.bind("<Key>", self.key)
        #import settings

        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        rel_path_settings = r"settings.ini"
        abs_path_settings = os.path.join(script_dir, rel_path_settings)
        self.settings = settings.Settings(abs_path_settings)
        #MainMenu init
        tkMainMenu = Menu(self.master)
        self.master.config(menu=tkMainMenu)
        tkMainManuMenuItemFile = Menu(tkMainMenu, tearoff=0)
        tkMainMenu.add_cascade(label="File", menu=tkMainManuMenuItemFile)
        tkMainMenu.add_command(label="About", command=lambda: CANLoaderAbout.MyDialog(self.master))
        #tkMainManuMenuItemAbout = Menu(tkMainMenu, tearoff=0)
        #tkMainManuMenuItemAbout.add_command(label="About program", command=lambda: CANLoaderAbout.MyDialog(self.master))
        tkMainManuMenuItemFile.add_command(label="Exit", command=lambda: self.master.destroy())

        #tkMainMenu.add_cascade(label="About", menu=tkMainManuMenuItemAbout)
        # allowing the widget to take the full space of the root window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #tabControlWidget
        tabControl = ttk.Notebook(self)
        tabProgramming = ttk.Frame(tabControl)
        tabSettings = ttk.Frame(tabControl)
        tabControl.add(tabProgramming, text="Programming")
        tabControl.add(tabSettings, text="Settings")

        tabControl.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=3, pady=3)
        tabControl.rowconfigure(0, weight=1)
        tabControl.columnconfigure(0, weight=1)
        tabProgramming.columnconfigure(0, weight=1)
        tabProgramming.rowconfigure(0, weight=1)    #frameCanDevice
        tabProgramming.rowconfigure(1, weight=1)    #frameProgramming
        tabProgramming.rowconfigure(2, weight=1)    #frameLog
        tabProgramming.rowconfigure(3, weight=1)    #statusBar
        # window positioning
        xpos = self.master.winfo_screenwidth() / 2 - defaultMainWindowSizeX / 2
        ypos = self.master.winfo_screenheight() / 2 - defaultMainWindowSizeY / 2
        self.master.geometry("+%d+%d" % (xpos, ypos))
        # set icon
        current_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(current_dir, r'Images\ico_canbus.ico')
        if os.path.exists(icon_path) and os.path.isfile(icon_path):
            self.master.iconbitmap(icon_path)
        # frameCanDevice configuring
        self.frameCanDevice = tk.LabelFrame(tabProgramming, relief=tk.RAISED, borderwidth=1, text="CAN Device")
        self.frameCanDevice.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameCanDevice.columnconfigure(0, weight=1, pad=3)
        self.frameCanDevice.columnconfigure(1, weight=1, pad=3)
        self.frameCanDevice.columnconfigure(2, weight=10, pad=3)
        self.frameCanDevice.columnconfigure(3, weight=1, pad=3)
        self.frameCanDevice.columnconfigure(4, weight=1, pad=3)
        self.frameCanDevice.rowconfigure(0, weight=1, pad=3)    #buttonFind and ListBox with found devices
        self.frameCanDevice.rowconfigure(1, weight=1, pad=3)    #frameFoundCanDevices

        self.buttonCanConnect = tk.Button(self.frameCanDevice,  wraplength=43, state="normal", text=r"CAN connect", command=self.buttonCANConnectClick)
        self.buttonCanConnect.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.buttonFind = tk.Button(self.frameCanDevice, wraplength=43, state="normal", text="Read", command=self.buttonFindClick)
        self.buttonFind.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameFoundCanDevices = tk.LabelFrame(self.frameCanDevice, relief=tk.RAISED, borderwidth=1, text="Devices Found")
        self.frameFoundCanDevices.grid(row=0, column=2, sticky=tk.N + tk.S + tk.W + tk.E,  padx=5, pady=5)
        self.frameFoundCanDevices.columnconfigure(0, weight=1, pad=3)
        self.frameFoundCanDevices.rowconfigure(0, weight=1, pad=3)
        self.comboboxFoundCanDevices = ttk.Combobox(self.frameFoundCanDevices, values=[
                                    "<devices not found>"], state="disable")
        self.comboboxFoundCanDevices.current(0)
        self.comboboxFoundCanDevices.bind("<<ComboboxSelected>>", self.comboboxFoundCanDevices_Selected)
        self.comboboxFoundCanDevices.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=1, pady=1)
        self.buttonLeaveBootloader = tk.Button(self.frameCanDevice, wraplength=43, state="normal", text="Leave Boot", command=self.buttonLeaveBootloaderClick)
        self.buttonLeaveBootloader.grid(row=0, column=3, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.buttonLock = tk.Button(self.frameCanDevice, wraplength=43, state="normal", text="Lock", command=self.buttonLockClick)
        self.buttonLock.grid(row=0, column=4, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)

        self.frameCanDeviceSelectedDevice = tk.LabelFrame(self.frameCanDevice, relief=tk.RAISED, borderwidth=1, text="Selected Device")
        self.frameCanDeviceSelectedDevice.grid(row=1, column=0, sticky=tk.N + tk.S + tk.W + tk.E, columnspan=5, padx=5, pady=5)
        self.frameCanDeviceSelectedDevice.columnconfigure(0, weight=1, pad=3)
        self.frameCanDeviceSelectedDevice.columnconfigure(1, weight=5, pad=3)
        self.frameCanDeviceSelectedDevice.columnconfigure(2, weight=1, pad=3)
        self.frameCanDeviceSelectedDevice.rowconfigure(0, weight=1, pad=3)
        self.frameCanDeviceSelectedDevice.rowconfigure(1, weight=1, pad=3)
        self.frameCanDeviceSelectedDevice.rowconfigure(2, weight=1, pad=3)
        self.frameCanDeviceSelectedDevice.rowconfigure(3, weight=1, pad=3)
        self.entryNodeIDText = tk.StringVar()
        self.entryNodeID = tk.Entry(self.frameCanDeviceSelectedDevice, state="disabled", textvariable=self.entryNodeIDText)
        self.entryNodeID.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, padx=3)
        #self.flashFilePath = tk.StringVar()
        #self.entryFlashFile = tk.Entry(self.frameProgramming, state="disabled", textvariable=self.flashFilePath)
        self.labelNodeID = tk.Label(self.frameCanDeviceSelectedDevice, text="Node ID:")
        self.labelNodeID.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.entryMCUInfoText = tk.StringVar()
        self.entryMCUInfo = tk.Entry(self.frameCanDeviceSelectedDevice, state="disabled", textvariable=self.entryMCUInfoText)
        self.entryMCUInfo.grid(row=1, column=1, sticky=tk.N + tk.S + tk.W + tk.E, padx=3)
        self.labelMCUInfo = tk.Label(self.frameCanDeviceSelectedDevice, text="MCU Info:")
        self.labelMCUInfo.grid(row=1, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.labelStatus = tk.Label(self.frameCanDeviceSelectedDevice, text="None")
        self.labelStatus.grid(row=0, column=2, sticky=tk.N + tk.S + tk.W + tk.E, rowspan=2)
        self.labelStatus.config(bg="gray")

        #frameProgramming configuring
        self.frameProgramming = tk.LabelFrame(tabProgramming, relief=tk.RAISED, borderwidth=1, text="Flash programming")
        self.frameProgramming.grid(row=1, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=3, pady=3)
        self.frameProgramming.columnconfigure(0, weight=1, pad=3)
        self.frameProgramming.columnconfigure(1, weight=1, pad=3)
        self.frameProgramming.columnconfigure(2, weight=1, pad=3)
        self.frameProgramming.columnconfigure(3, weight=1, pad=3)
        self.frameProgramming.columnconfigure(4, weight=1, pad=3)
        self.frameProgramming.columnconfigure(5, weight=1, pad=3)
        self.frameProgramming.rowconfigure(0, weight=1, pad=3)
        self.frameProgramming.rowconfigure(1, weight=1, pad=3)

        #frameLog configuring
        self.frameLog = tk.LabelFrame(tabProgramming, relief=tk.RAISED, borderwidth=1, text="Log")
        self.frameLog.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameLog.columnconfigure(0, weight=20, pad=3)
        self.frameLog.columnconfigure(1, weight=1, pad=3)
        self.frameLog.rowconfigure(0, weight=1, pad=3)
        self.flLstResults = tk.Listbox(self.frameLog)
        self.flLstResults.config(height=5)
        self.flLstResults.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)

        #statusBar configuring
        frameStatus = tk.Frame(tabProgramming, borderwidth=0)
        frameStatus.grid(row=3, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        frameStatus.columnconfigure(0, weight=1, pad=0)
        frameStatus.columnconfigure(1, weight=1, pad=0)
        frameStatus.rowconfigure(0, weight=1, pad=0)
        self.statusbarText = tk.StringVar()
        labelStatus = tk.Label(frameStatus, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                           textvariable=self.statusbarText)

        labelStatus.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        s = ttk.Style()
        s.theme_use('alt')
        s.configure("red.Horizontal.TProgressbar", foreground='red', background='green', padx=0, pady=0, pad=0)
        self.progressBar = ttk.Progressbar(frameStatus, mode="determinate", style="red.Horizontal.TProgressbar")
        self.progressBar.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E)
        self.progressBar['value'] = 0
        self.statusbarText.set('Started')

        labelInputFlash = tk.Label(self.frameProgramming, text="Input encoded .bin File")
        labelInputFlash.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.flashFilePath = tk.StringVar()
        self.entryFlashFile = tk.Entry(self.frameProgramming, state="disabled", textvariable=self.flashFilePath)
        self.entryFlashFile.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, columnspan=4)
        self.buttonSelectFlashFile = tk.Button(self.frameProgramming, state="disabled", text="...", command=self.buttonSelectFlashFileClick)
        self.buttonSelectFlashFile.grid(row=0, column=5, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)

        self.buttonProgramFlash = tk.Button(self.frameProgramming, state="disabled", text="Program", command=self.buttonProgramFlashClick)
        #self.buttonProgramFlash.config(state = "disabled")
        self.buttonProgramFlash.grid(row=1, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.buttonVerifyFlash = tk.Button(self.frameProgramming, state="disabled", text="Verify", command=self.buttonVerifyFlashClick)
        self.buttonVerifyFlash.grid(row=1, column=2, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.buttonReadFlash = tk.Button(self.frameProgramming, state="disabled", text="Read", command=self.buttonReadFlashClick)
        self.buttonReadFlash.grid(row=1, column=5, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)

        self.flLstResultsScrollbar = tk.Scrollbar(self.frameLog, orient=tk.VERTICAL)
        self.flLstResultsScrollbar.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, pady=5)

        self.flLstResults.config(yscrollcommand=self.flLstResultsScrollbar.set)
        self.flLstResultsScrollbar.config(command=self.flLstResults.yview)

        '''second tab - settings'''
        tabSettings.rowconfigure(0, weight=1)
        tabSettings.rowconfigure(1, weight=1)
        tabSettings.rowconfigure(2, weight=1)
        tabSettings.columnconfigure(0, weight=1)
        #CAN settings frame
        self.frameSettingsCAN = tk.LabelFrame(tabSettings, relief=tk.RAISED, borderwidth=1, text="CAN Settings")
        self.frameSettingsCAN.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameSettingsCAN.rowconfigure(0, weight=1)
        self.frameSettingsCAN.columnconfigure(0, weight=1)
        self.frameSettingsCAN.columnconfigure(1, weight=5)
        labelCANSpeed = tk.Label(self.frameSettingsCAN, text="CAN Baudrate:")
        labelCANSpeed.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.comboboxCANSpeed = ttk.Combobox(self.frameSettingsCAN, values=self.settings.getDisplayValue("CANBaudrates"), state="readonly")
        baudrate = self.settings.get("CAN", "BaudRate")
        if baudrate in self.comboboxCANSpeed['values']:
            self.comboboxCANSpeed.current(self.comboboxCANSpeed['values'].index(baudrate))
        else:
            self.comboboxCANSpeed.current(0)
        self.comboboxCANSpeed.bind("<<ComboboxSelected>>", self.comboboxCANSpeed_Selected)
        self.comboboxCANSpeed.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, padx=1, pady=1)
        #CANOpen settings frame
        self.frameSettingsCANOpen = tk.LabelFrame(tabSettings, relief=tk.RAISED, borderwidth=1, text="CANOpen Settings")
        self.frameSettingsCANOpen.grid(row=1, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)
        self.frameSettingsCANOpen.rowconfigure(0, weight=1)
        self.frameSettingsCANOpen.columnconfigure(0, weight=1)
        self.frameSettingsCANOpen.columnconfigure(1, weight=5)
        labelCANOpenId = tk.Label(self.frameSettingsCANOpen, text="CANOpen ID:")
        labelCANOpenId.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)

        self.comboboxCANOpenSelfId = ttk.Combobox(self.frameSettingsCANOpen, state="readonly", values = [c for c in range(1, 128)])
        nodeId = self.settings.get("CANOpen", "NodeID")
        self.comboboxCANOpenSelfId.grid(row=0, column=1, sticky=tk.N + tk.S + tk.W + tk.E, padx=1, pady=1)
        if nodeId in self.comboboxCANOpenSelfId['values']:
            self.comboboxCANOpenSelfId.current(self.comboboxCANOpenSelfId['values'].index(nodeId))
        else:
            self.comboboxCANOpenSelfId.current(0)
        self.comboboxCANOpenSelfId.bind("<<ComboboxSelected>>", self.comboboxCANOpenSelfId_Selected)
        self.labelNodeID = tk.Label(self.frameCanDeviceSelectedDevice, text="Node ID:")
        #Flash settings frame
        self.frameSettingsFlash = tk.LabelFrame(tabSettings, relief=tk.RAISED, borderwidth=1, text="Flash Settings")
        self.frameSettingsFlash.grid(row=2, column=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=5, pady=5)

        self.pack(fill=tk.BOTH, expand=tk.YES)

        self.__disable_controls__(self.frameCanDevice)
        self.buttonCanConnect.config(state="normal")

        self.__add_log_msg__("Started OK")
        self.__add_log_msg__('Press "' + self.buttonCanConnect['text'] + '" button to connect to the CAN network')
        self.master.protocol("WM_DELETE_WINDOW", self._delete_window)
        self.__workingAction = WorkingAction.wa_INIT
        self.__switch_controls__(te_OperationState.os_END)
        self.master.mainloop()
        # def buttonClick(self):
        # messagebox.showinfo("Say Hello", "Hello World")

    def _delete_window(self):
        try:
            del self.canLoaderController
        except Exception:
            pass
        else:
            self.__add_log_msg__('Ok! Thank you. Goodbye!')
        self.master.destroy()

    def buttonCANConnectClick(self):
        self.__switch_controls__(te_OperationState.os_BEGIN)
        try:
            self.canLoaderController = CANLoaderController(self.settings)
            self.labelStatus['text'] = "None"
            self.labelStatus.config(bg="gray")
        except CANfoxException as e:
            self.__workingAction = WorkingAction.wa_INIT
            self.__add_log_msg__(str(e))
        else:
            self.flLstResults.delete(0, tk.END)
            self.buttonCanConnect.configure(state='disable')
            self.buttonFind.configure(state='normal')
            self.__add_log_msg__('Successfully connected to CANfox transceiver. Press "' + self.buttonFind['text'] + '" button to discover devices')
            self.__workingAction = WorkingAction.wa_NONE
        self.__switch_controls__(te_OperationState.os_END)

    def buttonFindClick(self):
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
        self.flLstResults.insert(tk.END, "sieca_lib: " + str(self.sieca_lib))
             # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(res))
             # self.flLstResults.insert(tk.END, siecaDllInfo.aui_TxCounter)

        l_retval = self.sieca_lib.canSetBaudrate(self.siecaLibHandle,
                                                 int(CANTypeDefs.Baudrate.BAUD_250))  # 250 kbits/sec
        self.flLstResults.insert(tk.END, "Set Baudrate: " + str(CANTypeDefs.ReturnValues(l_retval)))
        l_retval = self.sieca_lib.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
        self.flLstResults.insert(tk.END, "LED flashing settings applied: " + str(CANTypeDefs.ReturnValues(l_retval)))
        l_retval = self.sieca_lib.canIsNetOwner(d_retval["handle"])
        self.flLstResults.insert(tk.END, "CanIsNetOwner: " + str(CANTypeDefs.ReturnValues(l_retval)))

        l_retval = self.sieca_lib.canSetFilterMode(self.siecaLibHandle, CANTypeDefs.T_FILTER_MODE.filterMode_nofilter)
        self.flLstResults.insert(tk.END, "CanSetFilterMode: " + str(CANTypeDefs.ReturnValues(l_retval)))
        message_reader = ThreadCANMsgReader(self.siecaLibHandle, self.sieca_lib, self.QueueIncomingMessages)
        message_reader.start()

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

        #self.process_queue()

        return
        '''for y in range(0, msg.by_len):
            s_data += "[" + str(y) + "] = " + str(hex(msg.aby_data[y])) + "; "
        self.flLstResults.insert(tk.END, "l_id: " + str(hex(msg.l_id)) + " by_len: " + str(
            msg.by_len) + " by_msg_lost: " + str(msg.by_msg_lost) +
                                 " by_extended: " + str(msg.by_extended) + " by_remote: " + str(
            msg.by_remote) + " ul_tstamp: " + str(msg.ul_tstamp) + " Data = " + s_data)'''

        """
        self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_Unknown
        self.buttonFind.configure(state='disable')
        self.flLstResults.delete(0, tk.END)
        self.__add_log_msg__('CANLoader devices searching...')
        try:
            nodes = self.canLoaderController.discover_connected_devices()
        except CANfoxHardwareException as e:
            self.__add_log_msg__("Hardware error: " + str(e))
            self.__switch_controls__(te_OperationState.os_END)
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
            self.StatusBarUpdaterFunction()
            return
        except Exception as e:
            self.__add_log_msg__("Software error: " + str(e))
            self.__switch_controls__(te_OperationState.os_END)
            self.__workingAction = WorkingAction.wa_ERROR
            self.StatusBarUpdaterFunction()
            return
        nodes.sort()
        nodes_text = "CAN IDs': "
        nodes_delimeter = ""
        for node_id in nodes:
            nodes_text = nodes_text + nodes_delimeter + ' {}'.format(str(node_id))
            nodes_delimeter = ","
        if len(nodes) != 0:
            self.__add_log_msg__("Found {} CAN devices(s): {}".format(len(nodes), nodes_text))
        else:
            self.__add_log_msg__("Any CANopen devices on CAN bus not found")
        try:
            self.reprogrammable_devices = self.canLoaderController.find_reprogrammable_devices()
        except CANfoxHardwareException as e:
            self.__add_log_msg__("Hardware error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
            self.__switch_controls__(te_OperationState.os_END)
            self.StatusBarUpdaterFunction()
            return
        except Exception as e:
            self.__add_log_msg__("Software error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
            self.__switch_controls__(te_OperationState.os_END)
            self.StatusBarUpdaterFunction()
            return

        if len(self.reprogrammable_devices) != 0:
            self.__add_log_msg__("Found {} CANOpen bootloader devices(s): ".format(len(self.reprogrammable_devices)))
            items = list()
            for iterator, node in self.reprogrammable_devices.items():
                programmable_nodes_text = "CANOpen ID: {}".format(node.id)
                items.append(
                    "NodeID: {}, Name(1008/0): {}".format(node.id, node._bag_['Manufacturer device name (0x1008_0)']))

                for node_param_desc, node_param_value in node._bag_.items():
                    programmable_nodes_text += ";{}={}".format(node_param_desc, node_param_value)
                self.__add_log_msg__(programmable_nodes_text)
            self.comboboxFoundCanDevices['values'] = items
            self.comboboxFoundCanDevices.current(0)

            self.entryNodeIDText.set('{}'.format(self.reprogrammable_devices[0].id))
            self.entryMCUInfoText.set('{}'.format(self.reprogrammable_devices[0]._bag_['Manufacturer device name (0x1008_0)']))
            self.labelStatus['text'] = "Ready"
            self.labelStatus.config(bg="green")
        else:
            self.__disable_controls__(self.frameCanDeviceSelectedDevice)
        self.__workingAction = WorkingAction.wa_NONE
        self.__switch_controls__(te_OperationState.os_END)
        self.buttonFind.configure(state='normal')
        return"""

    def check_my_msg(self):
        d_retval = self.sieca_lib.canRead(self.siecaLibHandle)

        for item in range(0, d_retval["l_len"].value):
            msg1 = d_retval["canmsg"][item]
        # msg2 = d_retval["canmsg"][0]
        s_data = ""
        # s_data = msg1.aby_data
        for y in range(0, msg1.by_len):
            s_data += str(hex(msg1.aby_data[y])) + " "
        self.__add_log_msg__(
            "[" + str(hex(msg1.l_id)) + "] Data = " + s_data + "; Len = " + str(msg1.by_len) + "; Ext: " + str(
                msg1.by_extended) + ";")
        self.master.after(100, self.check_my_msg)

    def buttonLeaveBootloaderClick(self):
        self.__workingAction = WorkingAction.wa_NONE
        self.__switch_controls__(te_OperationState.os_BEGIN)
        current_device = self.comboboxFoundCanDevices.current()
        try:
            self.canLoaderController.mcu_leave_bootloader(current_device)
        except CANLoaderDeviceFailureException as e:
            self.__add_log_msg__("Error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
        except Exception as e:
            self.__add_log_msg__("Error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        else:
            self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_Unknown
            self.__add_log_msg__("Left bootloader")
        self.StatusBarUpdaterFunction()
        self.__switch_controls__(te_OperationState.os_END)
        return

    def process_queue(self):
        try:
            while self.QueueIncomingMessages.qsize() > 0:
                #time.sleep(0.1)
                msg = self.QueueIncomingMessages.get(0)
                d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
                s_data = d_retval["canmsg"]
                self.__add_log_msg__("Data = " + str(s_data))
                '''self.flLstResults.insert(tk.END, "l_id: " + str(hex(msg.l_id)) + " by_len: " + str(
                    msg.by_len) + " by_msg_lost: " + str(msg.by_msg_lost) +
                                     " by_extended: " + str(msg.by_extended) + " by_remote: " + str(
                    msg.by_remote) + " ul_tstamp: " + str(msg.ul_tstamp) + " Data = " + s_data)'''
            #self.flLstResults.select_clear(self.flLstResults.size() - 2)  # Clear the current selected item
            #self.flLstResults.select_set(tk.END)  # Select the new item
                if self.flLstResults.size() > 100:
                    self.flLstResults.delete(0)
                self.flLstResults.yview(tk.END)  # Set the scrollbar to the end of the listbox
        except queue.Empty:
            pass #no data
        #self.master.after(100, self.process_queue)

    def buttonLockClick(self):
        current_device = self.comboboxFoundCanDevices.current()
        self.__workingAction = WorkingAction.wa_NONE
        self.__switch_controls__(te_OperationState.os_BEGIN)
        try:
            self.canLoaderController.move_mcu_to_bootloader(current_device)
            self.canLoaderController.mcu_lock(current_device)
        except CANLoaderDeviceFailureException as e:
            self.__add_log_msg__("Error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
        except Exception as e:
            self.__add_log_msg__("Error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        else:
            self.__add_log_msg__("Device locked")
            self.__workingAction = WorkingAction.wa_NONE
        self.StatusBarUpdaterFunction()
        self.__switch_controls__(te_OperationState.os_END)
        return

    def buttonSelectFlashFileClick(self):
        filename = filedialog.askopenfilename(initialdir="/", title="Select file",
                                              filetypes=(("Encoded bin file", "*.bin"), ("All files", "*.*")))
        if filename:
            self.__add_log_msg__("You has selected file: " + filename)
            try:
                filesize = os.path.getsize(filename)
                if os.path.exists(filename) and filesize > 0 and (filesize % 8 == 0):
                    self.flashFilePath.set(filename)
                else:
                    raise Exception('File not exists, empty, or corrupted.')
                if len(self.reprogrammable_devices) > 0:
                    self.__enable_controls_programming__()
            except Exception as e:
                self.__add_log_msg__("Error opening file: " + str(e))
        else:
            pass

    def FirmwareVerifierFunction(self):
        try:
            current_device = self.comboboxFoundCanDevices.current()
            self.canLoaderController.move_mcu_to_bootloader(current_device)
            self.QueueThreadVerifyingService.empty()
            self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_InBootloader
            self.canLoaderController.verify_firmware_file(current_device, self.flashFilePath, self.QueueProgressBar,
                                                      self.QueueThreadVerifyingService)
            self.__workingAction = WorkingAction.wa_NONE
            self.__add_log_msg__("Verifying completed successfully")
        except CANLoaderFirmwareVerifyException as e:
            self.__add_log_msg__("Verify error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        except CANfoxHardwareException as e:
            self.__add_log_msg__("Hardware error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
        except Exception as e:
            self.__add_log_msg__("Error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        else:
            self.__workingAction = WorkingAction.wa_NONE
        return

    def buttonVerifyFlashClick(self):
        self.__workingAction = WorkingAction.wa_VERIFYING
        self.__switch_controls__(te_OperationState.os_BEGIN)

        self.__add_log_msg__("Verifying target...")
        Thread(target=self.FirmwareVerifierFunction).start()
        self.master.after(250, self.StatusBarUpdaterFunction)
        self.labelStatus['text'] = "Verifying"
        self.labelStatus.config(bg="yellow")

    def FirmwareProgrammerFunction(self):
        try:
            current_device = self.comboboxFoundCanDevices.current()
            self.canLoaderController.move_mcu_to_bootloader(current_device)
            self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_InBootloader
            self.QueueThreadProgrammingService.empty()
            #0. Check Read/Write protection state of MCU. It's important - read_level2 and WrPr blocks are not accessible for this types of operation
            self.canLoaderController.reset_lock_state(current_device)
            self.__add_log_msg__("Device unlocked.")
            self.__add_log_msg__("Programming target...")
            self.canLoaderController.upload_firmware_file(current_device, self.flashFilePath, self.QueueProgressBar,
                                                          self.QueueThreadProgrammingService)
            self.__workingAction = WorkingAction.wa_NONE
            self.__add_log_msg__("Programming completed successfully")
        except CANLoaderFirmwareVerifyException as e:
            self.__add_log_msg__("CRC32 error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        except CANfoxHardwareException as e:
            self.__add_log_msg__("Hardware error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
        except Exception as e:
            self.__add_log_msg__("Programming error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        else:
            self.__workingAction = WorkingAction.wa_NONE
        return

    def StatusBarUpdaterFunction(self):
        try:
            while self.QueueProgressBar.qsize() > 0:
                progress = self.QueueProgressBar.get(0)
                self.progressBar['value'] = progress
                self.statusbarText.set("{:.2f}".format(progress) + "%")
        except queue.Empty:
            pass #no data
        if self.__workingAction == WorkingAction.wa_PROGRAMMING or \
                self.__workingAction == WorkingAction.wa_VERIFYING or \
            self.__workingAction == WorkingAction.wa_DEVICE_READING:
            self.master.after(250, self.StatusBarUpdaterFunction)
        elif self.__workingAction == WorkingAction.wa_NONE:
            self.progressBar['value'] = 0
            self.__add_log_msg__("Operation done")
            self.statusbarText.set("Operation done")
            self.labelStatus['text'] = "Ready"
            self.labelStatus.config(bg="green")
            self.__switch_controls__(te_OperationState.os_END)
        elif self.__workingAction == WorkingAction.wa_ERROR or self.__workingAction == WorkingAction.wa_HARDWARE_ERROR:
            self.labelStatus['text'] = "Error"
            self.labelStatus.config(bg="red")
            self.__switch_controls__(te_OperationState.os_END)
        return

    def buttonProgramFlashClick(self):
        self.__workingAction = WorkingAction.wa_PROGRAMMING
        self.__switch_controls__(te_OperationState.os_BEGIN)
        self.__add_log_msg__("Move to bootloader: done.")
        # creating new thread for sync operations
        Thread(target=self.FirmwareProgrammerFunction).start()
        self.master.after(250, self.StatusBarUpdaterFunction)
        self.labelStatus['text'] = "Programming"
        self.labelStatus.config(bg="blue")
        return

    def FirmwareReaderFunction(self, saveFilePath):
        try:
            current_device = self.comboboxFoundCanDevices.current()
            self.canLoaderController.move_mcu_to_bootloader(current_device)
            self.QueueThreadReadingService.empty()
            self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_InBootloader
            self.canLoaderController.download_firmware_file(current_device, saveFilePath, self.QueueProgressBar,
                                                            self.QueueThreadReadingService)
            self.__workingAction = WorkingAction.wa_NONE
            self.__add_log_msg__("Reading completed successfully")
        except CANfoxHardwareException as e:
            self.__add_log_msg__("Hardware error: " + str(e))
            self.__workingAction = WorkingAction.wa_HARDWARE_ERROR
        except Exception as e:
            self.__add_log_msg__("Reading error: " + str(e))
            self.__workingAction = WorkingAction.wa_ERROR
        else:
            self.__workingAction = WorkingAction.wa_NONE
        return

    def buttonReadFlashClick(self):
        filename = filedialog.asksaveasfilename(initialdir="/", title="Select file to save encoded firmware data",
                                              filetypes=(("Encoded bin file", "*.bin"), ("All files", "*.*")))
        if len(filename) != 0 and os.access(os.path.dirname(filename), os.W_OK):
            current_device = self.comboboxFoundCanDevices.current()
            self.canLoaderController.move_mcu_to_bootloader(current_device)
            self.__add_log_msg__("Move to bootloader: done.")
            # creating new thread for sync operations
            self.__workingAction = WorkingAction.wa_DEVICE_READING
            self.__switch_controls__(te_OperationState.os_BEGIN)
            self.__add_log_msg__("Reading target...")
            Thread(target=self.FirmwareReaderFunction, args=(filename,)).start()
            self.master.after(250, self.StatusBarUpdaterFunction)
            self.labelStatus['text'] = "Reading"
            self.labelStatus.config(bg="aqua")
        else:
            if len(filename) != 0:
                self.__add_log_msg__("Loader not write permission for (administrator rights?): " + str(filename))

    #events
    def comboboxFoundCanDevices_Selected(self, event):
        self.CurrentDeviceBootloaderState = te_CurrentDeviceBootloaderState.bs_Unknown

        return

    def comboboxCANSpeed_Selected(self, event):
        baudrate = self.comboboxCANSpeed['values'][self.comboboxCANSpeed.current()]
        self.settings.set("CAN", "BaudRate", baudrate)
        return

    def comboboxCANOpenSelfId_Selected(self, event):
        nodeid = self.comboboxCANOpenSelfId['values'][self.comboboxCANOpenSelfId.current()]
        self.settings.set("CANOpen", "NodeID", nodeid)
        return

    def client_exit(self):
        self.master.destroy()
        return





def WinMain():
    root = tk.Tk()
    # size of the window

    # MainApplication(root).pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
    app = MainApplication(root)
    # sizexx = app.winfo_width()


if __name__ == "__main__":
    WinMain()



    '''def process_queue(self):
        try:
            while self.QueueIncomingMessages.qsize() > 0:
                msg = self.QueueIncomingMessages.get(0)
                s_data = ""
                for y in range(0, msg.by_len):
                    s_data += "[" + str(y) + "] = " + str(hex(msg.aby_data[y])) + "; "
                self.flLstResults.insert(tk.END, "l_id: " + str(hex(msg.l_id)) + " by_len: " + str(
                    msg.by_len) + " by_msg_lost: " + str(msg.by_msg_lost) +
                                     " by_extended: " + str(msg.by_extended) + " by_remote: " + str(
                    msg.by_remote) + " ul_tstamp: " + str(msg.ul_tstamp) + " Data = " + s_data)
            #self.flLstResults.select_clear(self.flLstResults.size() - 2)  # Clear the current selected item
            #self.flLstResults.select_set(tk.END)  # Select the new item
                if self.flLstResults.size() > 100:
                    self.flLstResults.delete(0)
                self.flLstResults.yview(tk.END)  # Set the scrollbar to the end of the listbox
        except queue.Empty:
            pass #no data
        self.master.after(100, self.process_queue)
'''

    '''self.sieca_lib = sieca132_client()

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
     self.flLstResults.insert(tk.END, "sieca_lib: " + str(self.sieca_lib))
     # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(res))
     # self.flLstResults.insert(tk.END, siecaDllInfo.aui_TxCounter)

     l_retval = self.sieca_lib.canSetBaudrate(self.siecaLibHandle,
                                              int(CANTypeDefs.Baudrate.BAUD_250))  # 250 kbits/sec
     self.flLstResults.insert(tk.END, "Set Baudrate: " + str(CANTypeDefs.ReturnValues(l_retval)))
     sleep(5)
     l_retval = self.sieca_lib.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
     self.flLstResults.insert(tk.END, "LED flashing settings applied: " + str(CANTypeDefs.ReturnValues(l_retval)))
     l_retval = self.sieca_lib.canIsNetOwner(d_retval["handle"])
     self.flLstResults.insert(tk.END, "CanIsNetOwner: " + str(CANTypeDefs.ReturnValues(l_retval)))

     l_retval = self.sieca_lib.canSetFilterMode(self.siecaLibHandle, CANTypeDefs.T_FILTER_MODE.filterMode_nofilter)
     self.flLstResults.insert(tk.END, "CanSetFilterMode: " + str(CANTypeDefs.ReturnValues(l_retval)))
     message_reader = ThreadCANMsgReader(self.siecaLibHandle, self.sieca_lib, self.QueueIncomingMessages)
     message_reader.start()
     # d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
     # self.flLstResults.insert(tk.END, "DataCount: " + str(d_retval["l_len"]))
     # self.flLstResults.insert(tk.END, "DataCount: " + str(CANTypeDefs.ReturnValues(d_retval["l_retval"])))

     self.process_queue()'''

    '''for x in range(0, d_retval["l_len"].value):
        canmessage = d_retval["canmsg"][x]
        # canmessage.aby_data
        s_data = ""
        for y in range(0, canmessage.by_len):
            s_data += "[" + str(y) + "] = " + str(hex(canmessage.aby_data[y])) + "; "

        self.flLstResults.insert(tk.END, "l_id: " + str(hex(canmessage.l_id)) + " by_len: " + str(
            canmessage.by_len) + " by_msg_lost: " + str(canmessage.by_msg_lost) +
                                 " by_extended: " + str(canmessage.by_extended) + " by_remote: " + str(
            canmessage.by_remote) + " ul_tstamp: " + str(canmessage.ul_tstamp) + " Data = " + s_data)

    # l_retval = sieca_lib.canClose(d_retval["handle"])
    # self.flLstResults.insert(tk.END, CANTypeDefs.ReturnValues(l_retval))
    '''