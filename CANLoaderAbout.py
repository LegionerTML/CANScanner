from tkinter import *
import os

class MyDialog:

    def __init__(self, parent):

        top = self.top = Toplevel(parent)
        defaultMainWindowSizeX = 200
        defaultMainWindowSizeY = 200
        top.geometry(str(defaultMainWindowSizeX) + "x" + str(defaultMainWindowSizeY))
        xpos = parent.winfo_screenwidth() / 2 - defaultMainWindowSizeX / 2
        ypos = parent.winfo_screenheight() / 2 - defaultMainWindowSizeY / 2
        top.geometry("+%d+%d" % (xpos, ypos))
        top.title("CANLoader: About")

        Label(top, text="CANLoader is designed\n for programming flash memory\n of microcontrollers over the CAN\n interface using CANOpen as\n the high-level protocol.").pack()
        b = Button(top, text="OK", command=self.ok)
        b.pack(pady=5)
        Label(top, text="Authors: Good luck!").pack()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(current_dir, r'Images\ico_canbus.ico')
        if os.path.exists(icon_path) and os.path.isfile(icon_path):
            top.iconbitmap(icon_path)
        top.transient(parent)
        top.grab_set()
        top.focus_set()
        top.wait_window()

    def ok(self):
        self.top.destroy()


#root = Tk()
#Button(root, text="Hello!").pack()
#root.update()

