import ctypes
import ctypes.wintypes
import os
import copy

import CANTypeDefs


class sieca132_client(object):
    def __init__(self):
        self.lib = ctypes.WinDLL(os.path.join(os.path.dirname(__file__), 'SIECA132.DLL'))
        return

    def canStatus(self, handle):
        canStatus = CANTypeDefs.CAN_IF_STATUS()
        self.lib.canStatus.restype = ctypes.c_long
        self.lib.canStatus.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(CANTypeDefs.CAN_IF_STATUS)]
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        l_retval = self.lib.canStatus(addr, ctypes.byref(canStatus))
        d_retval = dict()
        d_retval["l_retval"] = l_retval
        d_retval["can_status"] = canStatus
        return d_retval

    def canGetDllInfo(self):
        return self.request32('canGetDllInfo')

    def canIdAdd(self, handle, l_id):
        return self.request32('canIdAdd', handle, l_id)

    def canOpen(self, l_netnumber, l_mode, l_echoon, l_txtimeout, l_rxtimeout, c_Applicationname, c_ReceiverEvent, c_ErrorEvent):
        c_Applicationname = ctypes.c_char_p(str.encode(c_Applicationname))
        c_ReceiverEvent = ctypes.c_char_p(str.encode(c_ReceiverEvent))
        c_ErrorEvent = ctypes.c_char_p(str.encode(c_ErrorEvent))

        handle = ctypes.wintypes.HANDLE()
        self.lib.canOpen.restype = ctypes.c_long
        self.lib.canOpen.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long, ctypes.c_long, ctypes.c_long,
                                     ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p]
        handle = ctypes.cast(handle, ctypes.c_void_p)
        l_retval = self.lib.canOpen(l_netnumber, l_mode, l_echoon, l_txtimeout, l_rxtimeout, c_Applicationname,
                                c_ReceiverEvent, c_ErrorEvent, ctypes.byref(handle))
        handle = ctypes.cast(ctypes.addressof(handle), ctypes.POINTER(ctypes.c_int)).contents.value
        d_retval = dict()
        d_retval["handle"] = handle
        d_retval["l_retval"] = l_retval
        return d_retval

    def canClose(self, handle):
        self.lib.canClose.argtypes = [ctypes.wintypes.HANDLE]
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.c_void_p))
        return self.lib.canClose(addr)

    def canSetBaudrate(self, handle, l_baud):
        self.lib.canSetBaudrate.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_long]
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        return self.lib.canSetBaudrate(addr, l_baud)

    def canBlinkLED(self, handle, ulMode, ulStatus, ulPattern):
        self.lib.canBlinkLED.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        return self.lib.canBlinkLED(addr, ulMode, ulStatus, ulPattern)

    def canIsNetOwner(self, handle):
        self.lib.canIsNetOwner.argtypes = [ctypes.wintypes.HANDLE]
        self.lib.canIsNetOwner.restype = ctypes.c_long
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        return self.lib.canIsNetOwner(addr)

    def canSetFilterMode(self, handle, t_mode):
        self.lib.canIsNetOwner.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_long]
        self.lib.canIsNetOwner.restype = ctypes.c_long
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        return self.lib.canSetFilterMode(addr, int(t_mode))

    def canRead(self, handle):
        self.lib.canRead.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.canRead.restype = ctypes.c_long
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        l_len = ctypes.c_long(1)
        canmsg = (CANTypeDefs.CMSG * 1)()
        l_retval = self.lib.canRead(addr, ctypes.byref(canmsg), ctypes.byref(l_len))
        d_retval = dict()
        d_retval["l_len"] = l_len
        d_retval["l_retval"] = l_retval
        canmsg = [canmsg[i] for i in range(l_len.value)]

        d_retval["canmsg"] = canmsg
        return d_retval

    def canReadNoWait(self, handle):
        self.lib.canRead.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(ctypes.c_long)]
        self.lib.canRead.restype = ctypes.c_long
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        l_len = ctypes.c_long(1)
        canmsg = (CANTypeDefs.CMSG * 1)()
        l_retval = self.lib.canReadNoWait(addr, ctypes.byref(canmsg), ctypes.byref(l_len))
        d_retval = dict()
        d_retval["l_len"] = l_len
        d_retval["l_retval"] = l_retval
        canmsg = [canmsg[i] for i in range(l_len.value)]
        d_retval["canmsg"] = canmsg
        return d_retval

    def canConfirmedTransmit(self, handle, cmsg, l_len):
        return self.request32('canConfirmedTransmit', handle, cmsg, l_len)

    def canSend(self, handle, cmsg, l_len):
        self.lib.canSend.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(CANTypeDefs.CMSG),
                                     ctypes.POINTER(CANTypeDefs.c_long)]
        self.lib.canSend.restype = ctypes.c_long
        addr = ctypes.cast(handle, ctypes.POINTER(ctypes.wintypes.HANDLE))
        canmsg = copy.copy(cmsg)
        l_len_ctypes = ctypes.c_long(l_len)
        return self.lib.canSend(addr, ctypes.byref(canmsg), ctypes.byref(l_len_ctypes))

    def canWrite(self, handle, cmsg, l_len):
        return self.canSend(handle, cmsg, l_len)
