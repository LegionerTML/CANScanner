import CANTypeDefs
import ctypes
from can import CanError, BusABC, Message
import platform
if platform.architecture()[0] == '32bit':
    from sieca132_client_x32 import sieca132_client
else:
    from sieca132_client_x64 import sieca132_client

import logging
import threading
import canopen
import ThreadCANMsgReader
import settings
log = logging.getLogger('can.CANFox')


BaudrateConverter = {"20 kBit/s": CANTypeDefs.Baudrate.BAUD_20,
                     "50 kBit/s": CANTypeDefs.Baudrate.BAUD_50,
                     "100 kBit/s": CANTypeDefs.Baudrate.BAUD_100,
                     "125 kBit/s": CANTypeDefs.Baudrate.BAUD_125,
                    "250 kBit/s": CANTypeDefs.Baudrate.BAUD_250,
                    "500 kBit/s": CANTypeDefs.Baudrate.BAUD_500,
                    "800 kBit/s": CANTypeDefs.Baudrate.BAUD_800,
                    "1000 kBit/s": CANTypeDefs.Baudrate.BAUD_1000}

class CANFoxLibSkin(BusABC):
    """The CAN Bus implemented for the CANFox interface.

    .. warning::

        This interface does implement efficient filtering of messages, but
        the filters have to be set in :meth:`~can.interfaces.canfox.CANFoxBus.__init__`
        using the ``can_filters`` parameter. Using :meth:`~can.interfaces..canfox.CANFoxBus.set_filters`
        does not work.
"""

    def __init__(self, *args, **kwargs):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param bool receive_own_messages:
            Enable self-reception of sent messages.

        :param int UniqueHardwareId:
            UniqueHardwareId to connect (optional, will use the first found if not supplied)

        :param int bitrate:
            Channel bitrate in bit/s
        """
        if sieca132_client is None:
            raise ImportError("The CANfox library has not been initialized. Check library settings.")

        try:
            self.sieca_client = sieca132_client()
        except Exception as e:
            log.warning("Cannot load SIECA132.dll library: %s", e)
            raise CANfoxException('Cannot load SIECA132.dll library: {0}'.format(e))
        else:
            self.settings = kwargs['settings']

        l_netnumber = 105
        l_txtimeout = -1
        l_rxtimeout = -1

        c_canAppName = "CANUpdateManager"
        c_ReceiverEventName = "RE1"
        c_ErrorEventName = "EE1"
        self.lib_mutex = threading.Lock()
        self.lib_mutex.acquire()
        result = self.sieca_client.canOpen(l_netnumber, 0, 0, l_txtimeout, l_rxtimeout, c_canAppName,
                                          c_ReceiverEventName, c_ErrorEventName)
        if CANTypeDefs.ReturnValues(result["l_retval"]) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            raise CANfoxException(str(platform.architecture()[0]) + "CANFox initialization error: " + str(CANTypeDefs.ReturnValues(result["l_retval"])))


        self.siecaLibHandle = result["handle"]
        baudrate = BaudrateConverter[self.settings.get("CAN", "BaudRate")]
        result = self.sieca_client.canSetBaudrate(self.siecaLibHandle,
                                                 baudrate.value)  # 250 kbits/sec
        if CANTypeDefs.ReturnValues(result) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            #ebaud = self.sieca_client.canStatus(self.siecaLibHandle)
            raise CANfoxException("Set CAN baudrate error: " + str(CANTypeDefs.ReturnValues(result)))   #str(ebaud) +

        self.sieca_client.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
        self.sieca_client.canIsNetOwner(self.siecaLibHandle)
        self.sieca_client.canSetFilterMode(self.siecaLibHandle, CANTypeDefs.T_FILTER_MODE.filterMode_nofilter)
        self.lib_mutex.release()
        #result = self.sieca_client.canIdAdd(self.siecaLibHandle, 1)
        #if CANTypeDefs.ReturnValues(result) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            #raise CANfoxException("Error CAN add ID: " + str(CANTypeDefs.ReturnValues(result)))

        #result = self.sieca_client.canStatus(self.siecaLibHandle)
        #if CANTypeDefs.ReturnValues(result["l_retval"]) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
           #raise CANfoxException("getStatus error: " + str(CANTypeDefs.ReturnValues(result["l_retval"])))
        #message_reader = ThreadCANMsgReader(self.siecaLibHandle, self.sieca_lib, self.QueueIncomingMessages)
        #message_reader.start()
        # d_retval = self.sieca_lib.canRead(self.siecaLibHandle)
        # self.flLstResults.insert(tk.END, "DataCount: " + str(d_retval["l_len"]))
        # self.flLstResults.insert(tk.END, "DataCount: " + str(CANTypeDefs.ReturnValues(d_retval["l_retval"])))

        #self.process_queue()


    def CANfoxBLINK(self, isBlink):
        if isBlink == 0:
            self.sieca_client.canBlinkLED(self.siecaLibHandle, 2, 0b111, 0b001)
            return 1
        else:
            self.sieca_client.canBlinkLED(self.siecaLibHandle, 0, 0b111, 0b101)
            return 0


    def recv_sync(self):
        self.lib_mutex.acquire()
        result = self.sieca_client.canRead(self.siecaLibHandle)
        self.lib_mutex.release()
        if CANTypeDefs.ReturnValues(result["l_retval"]) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            raise CANfoxException("canRead error: " + str(CANTypeDefs.ReturnValues(result["l_retval"])))
        if result["l_len"].value !=0:
            foxmsg = result["canmsg"][0]
            msg = Message(timestamp = foxmsg.ul_tstamp,
                          arbitration_id = foxmsg.l_id,
                          dlc=foxmsg.by_len,
                          data=foxmsg.aby_data)
            return msg
        else:
            return None

    def recv_async(self):
        #time.sleep(0.01)
        self.lib_mutex.acquire()
        result = self.sieca_client.canReadNoWait(self.siecaLibHandle)
        self.lib_mutex.release()
        if CANTypeDefs.ReturnValues(result["l_retval"]) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS and CANTypeDefs.ReturnValues(result["l_retval"]) != CANTypeDefs.ReturnValues.NTCAN_RX_TIMEOUT:
            raise CANfoxException("canRead error: " + str(CANTypeDefs.ReturnValues(result["l_retval"])))
        if result["l_len"].value != 0:
            foxmsg = result["canmsg"][0]
            msg = Message(timestamp=foxmsg.ul_tstamp,
                              arbitration_id=foxmsg.l_id,
                              dlc=foxmsg.by_len,
                              data=foxmsg.aby_data)
            return msg
        else:
            return None


        #for item in range(0, result["l_len"].value):
            #self.queue.put(result["canmsg"][item])
        '''for y in range(0, msg.by_len):
            s_data += "[" + str(y) + "] = " + str(hex(msg.aby_data[y])) + "; "
        self.flLstResults.insert(tk.END, "l_id: " + str(hex(msg.l_id)) + " by_len: " + str(
            msg.by_len) + " by_msg_lost: " + str(msg.by_msg_lost) +
                                 " by_extended: " + str(msg.by_extended) + " by_remote: " + str(
            msg.by_remote) + " ul_tstamp: " + str(msg.ul_tstamp) + " Data = " + s_data)'''

        '''class CMSG(Structure):
    _fields_ = [
        ("l_id", c_long),
        ("by_len", c_ubyte),
        ("by_msg_lost", c_ubyte),
        ("by_extended", c_ubyte),
        ("by_remote", c_ubyte),
        ("aby_data", c_ubyte * 8),
        ("ul_tstamp", c_ulong)
    ]'''
    def send(self, msg, timeout=None):
        canmsg = CANTypeDefs.CMSG()

        canmsg.l_id = msg.arbitration_id
        canmsg.by_len = msg.dlc

        databyteArray = bytearray(msg.data)

        canmsg.aby_data[:] = databyteArray
        canmsg.by_extended = 0
        canmsg.by_remote = 0
        self.lib_mutex.acquire()

        result = self.sieca_client.canSend(self.siecaLibHandle, canmsg, 1)

        self.lib_mutex.release()
        #result = self.sieca_client.canConfirmedTransmit(self.siecaLibHandle, canmsg, 1)
        if CANTypeDefs.ReturnValues(result) == CANTypeDefs.ReturnValues.NTCAN_HARDWARE_NOT_FOUND:
            raise CANfoxHardwareException("USB adapter not found")
        elif CANTypeDefs.ReturnValues(result) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            raise CANfoxException("CANFox canSend(): " + str(CANTypeDefs.ReturnValues(result)))


    def shutdown(self):
        self.lib_mutex.acquire()
        result = self.sieca_client.canClose(self.siecaLibHandle)
        self.lib_mutex.release()

        if CANTypeDefs.ReturnValues(result) != CANTypeDefs.ReturnValues.NTCAN_SUCCESS:
            raise CANfoxException("Error CANFox canClose(): " + str(CANTypeDefs.ReturnValues(result)))

    def hardware_is_available(self):
        l_netnumber = 100
        l_txtimeout = -1
        l_rxtimeout = -1

        c_canAppName = "CANTestService"
        c_ReceiverEventName = "RE2"
        c_ErrorEventName = "EE2"
        self.lib_mutex.acquire()
        result = self.sieca_client.canOpen(l_netnumber, 0, 0, l_txtimeout, l_rxtimeout, c_canAppName,
                                           c_ReceiverEventName, c_ErrorEventName)
        libHandleForTest = result["handle"]
        self.sieca_client.canClose(libHandleForTest)
        self.lib_mutex.release()

        if CANTypeDefs.ReturnValues(result["l_retval"]) == CANTypeDefs.ReturnValues.NTCAN_HARDWARE_NOT_FOUND:
            self.shutdown()
            raise CANfoxHardwareException("Hardware failure")
        else:
            raise canopen.sdo.exceptions.SdoCommunicationError("Device not answered")

class CANfoxException(Exception):
    pass

class CANfoxHardwareException(Exception):
    pass