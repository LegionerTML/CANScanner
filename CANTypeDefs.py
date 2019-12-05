from ctypes import *
from enum import Enum

# https://docs.python.org/3/library/ctypes.html

MAX_NUM_APIHANDLE = 3
UP_DATA_PACKET_SIZE  = 21


class st_InternalDLLInformation(Structure):
    _fields_ = [
        ("aui_TxCounter", c_uint * 2),
        ("aui_TxHandleCounter", c_uint * MAX_NUM_APIHANDLE),
        ("aui_TxCounterRTR", c_uint * 2),
        ("aui_TxHandleCounterRTR", c_uint * MAX_NUM_APIHANDLE),
        ("aui_TxThreadCounter", c_uint * 2),
        ("aui_TxThreadCounterRTR", c_uint * 2),
        ("aui_RxCounter", c_uint * MAX_NUM_APIHANDLE),
        ("aui_RxThreadCounter", c_uint * 2),
        ("aui_RxBufferCounter", c_uint * MAX_NUM_APIHANDLE),
        ("aui_InterfaceCtr", c_uint * MAX_NUM_APIHANDLE),
        ("appNames", c_void_p),
        ("aui_ThreadStatus", c_uint * MAX_NUM_APIHANDLE),
        ("aui_ZugriffsCounterRead", c_uint * MAX_NUM_APIHANDLE),
        ("aui_ZugriffsCounterWrite", c_uint * MAX_NUM_APIHANDLE),
        ("aui_HandleNr", c_uint * MAX_NUM_APIHANDLE),
        ("aui_NetzZuordnung", c_uint * MAX_NUM_APIHANDLE),
        ("aui_NetzOwner", c_uint * 2),
        ("aui_Reserve1601", c_uint * MAX_NUM_APIHANDLE),
        ("aui_Reserve1602", c_uint * MAX_NUM_APIHANDLE),
        ("aui_Reserve1603", c_uint * MAX_NUM_APIHANDLE),
        ("aui_Reserve1604", c_uint * MAX_NUM_APIHANDLE),
        ("ui_NetCount", c_uint),
        ("ui_Reserve", c_uint),
        ("aui_AnzahlEchoFrames", c_uint * 2),
        ("ui_CloseZaehler", c_uint),
        ("ui_OpenZaehler", c_uint),
        ("ui_CloseFlag", c_uint),
        ("ui_OpenedHandles", c_uint)
    ]


class CMSG(Structure):
    _fields_ = [
        ("l_id", c_long),
        ("by_len", c_ubyte),
        ("by_msg_lost", c_ubyte),
        ("by_extended", c_ubyte),
        ("by_remote", c_ubyte),
        ("aby_data", c_ubyte * 8),
        ("ul_tstamp", c_ulong)
    ]

class CAN_IF_STATUS(Structure):
    _fields_ = [
        ("w_hw_rev", c_ushort),
        ("w_fw_rev", c_ushort),
        ("w_drv_rev", c_ushort),
        ("w_dll_rev", c_ushort),
        ("ul_board_status", c_ulong),
        ("by_board_id", c_uint8),
        ("w_busoffctr", c_ushort),
        ("w_errorflag", c_ushort),
        ("w_errorframectr", c_ushort),
        ("w_netctr", c_ushort),
        ("w_baud", c_ushort),
        ("w_baud", c_uint),
    ]


class ReturnValues(Enum):
    NTCAN_SUCCESS = 0
    NTCAN_RX_TIMEOUT = -1
    NTCAN_TX_TIMEOUT = -2
    NTCAN_CONTR_BUSOFF = -3
    NTCAN_NO_ID_ENABLED = -4
    NTCAN_ID_ALREADY_ENABLED = -5
    NTCAN_ID_NOT_ENABLED = -6
    NTCAN_INVALID_PARAMETER = -7
    NTCAN_INVALID_HANDLE = -8
    NTCAN_TOO_MANY_HANDLES = -9
    NTCAN_INIT_ERROR = -10
    NTCAN_RESET_ERROR = -11
    NTCAN_DRIVER_ERROR = -12
    NTCAN_DLL_ALREADY_INIT = -13
    NTCAN_CHANNEL_NOT_INITIALIZED = -14
    NTCAN_TX_ERROR = -15
    NTCAN_NO_SHAREDMEMORY = -16
    NTCAN_HARDWARE_NOT_FOUND = -17
    NTCAN_INVALID_NETNUMBER = -18
    NTCAN_TOO_MANY_J2534_RANGES = -19
    NTCAN_TOO_MANY_J2534_2_FILTERS = -20
    NTCAN_DRIVER_NOT_INSTALLED = -21
    NTCAN_NO_OWNER_RIGHTS = -22
    NTCAN_FIRMWARE_TOO_OLD = -23
    NTCAN_FIRMWARE_UNSUPPORTED = -24
    NTCAN_FIRMWAREUPDATE_FAILED = -25
    NTCAN_HARDWARE_NOT_SUPPORTED = -26
    NTCAN_FILE_NOT_FOUND = -27
    NTCAN_DEVICE_INFO_NOTAVAILABLE = -100
    NTCAN_DEVICE_NOHW_ADDRESS = -101
    NTCAN_NO_INTERRUPT_EVENT = -102
    NTCAN_NO_INTERRUPT_EVENT_SET = -103
    NTCAN_GET_MUTEX_FAILED = -104
    NTCAN_NO_SHARED_MEMORY = -105
    NTCAN_NET_NOT_AVAILABLE = -106
    NTCAN_SETBAUDRATE_TIMEOUT = -107
    NTCAN_EXE_ALREADYSTARTED = -108
    NTCAN_NOTABLE_TOCREATE_SHAREDMEMORY = -109
    NTCAN_HARDWARE_IN_USE = -110
    NTCAN_API_NOT_RUNNING = -111
    NTCAN_CHANNEL_CURR_NOT_AVAILABLE = -112
    NTCAN_BUFFER_TOO_SMALL = -113
    NTCAN_TOO_MANY_BRIDGE_FILTER = -114
    NTCAN_HARDWARENOTACTIVE = -200
    NTCAN_TOO_MANY_APPLICATIONS = -201
    NTCAN_NOSUCCESS = 0xFFFF0000


class Baudrate(Enum):
    BAUD_1000 = 0x00000000
    BAUD_800 = 0x00000001
    BAUD_500 = 0x00000002
    BAUD_250 = 0x00000003
    BAUD_125 = 0x00000004
    BAUD_100 = 0x00000005
    BAUD_50 = 0x00000006
    BAUD_20 = 0x00000007

    def __int__(self):
        return self.value

class T_FILTER_MODE(Enum):
    filterMode_standard = 0
    filterMode_j2534 = 1
    filterMode_extended = 2
    filterMode_j2534_2 = 3
    filterMode_nofilter = 4

    @classmethod
    def from_param(cls, obj):
        return int(obj)

    def __int__(self):
        return self.value


class T_CANOPEN_OD_INDEX(Enum):
    DeviceType = 0x1000
    ManufacturerDeviceName = 0x1008
    ManufacturerHardwareVersion = 0x1009
    ManufacturerSoftwareVersion = 0x100A
    Identity = 0x1018
    DownloadProgramData = 0x1F50    #cia302
    ProgramControl = 0x1F51
    ExpectedApplicationSWDate = 0x1F52
    ExpectedApplicationSWTime = 0x1F53

    def __int__(self):
        return self.value
    # Option 1: set the _as_parameter value at construction.
   # def __init__(self, value):
        #self._as_parameter = int(value)


class T_CANOPEN_PROGRAM_INDEX(Enum):
    Bootloader = 1
    MainProgram = 2

    def __int__(self):
        return self.value

class T_CANOPEN_PROGRAM_STATE(Enum):
    Stopped = 0
    LaunchCommandSent = 1
    Started = 2
    def __int__(self):
        return self.value

class T_CommandPacketTypeException(Exception):
    pass

class T_CommandPacketType(Enum):
    pt_ReadSignature = 0
    pt_ReadFlash = 1
    pt_WriteFlashEncoded = 2
    pt_WriteFlashDecoded = 3
    pt_WriteEEPROM = 4
    pt_CheckCrc = 5
    pt_Lock = 6
    pt_LeaveBootloader = 7
    pt_AesReset = 8
    pt_ErrorState = 9

    def __int__(self):
        return self.value

UP_PAYLOAD_WITH_ADDRESS_SIZE = (UP_DATA_PACKET_SIZE - sizeof(c_uint32) - sizeof(c_uint8))
UP_PAYLOAD_WITH_TWO_ADDRESSES_SIZE = (UP_PAYLOAD_WITH_ADDRESS_SIZE - sizeof(c_uint32))
UP_PAYLOAD_ONLY_COMMAND_SIZE = (UP_DATA_PACKET_SIZE - sizeof(c_uint8))
UP_DATA_LOCKPACKET_REQUEST_U8_DATA_SIZE = (UP_PAYLOAD_ONLY_COMMAND_SIZE - sizeof(c_uint8)*2)
UP_DATA_LOCKPACKET_RESPONSE_U8_DATA_SIZE = (UP_PAYLOAD_ONLY_COMMAND_SIZE - sizeof(c_uint8) - sizeof(c_uint32))
UP_DATA_PACKET_ERROR_DATA_SIZE = (UP_PAYLOAD_ONLY_COMMAND_SIZE - sizeof(c_uint8)*2)

class T_UpPacket(Structure):
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("data", c_uint8 * UP_PAYLOAD_ONLY_COMMAND_SIZE)
    ]
    def __init__(self, firmware_data):
        super(T_UpPacket, self).__init__()
        self.command = int.from_bytes(firmware_data[:1], byteorder='big')
        return

class T_UpWriteEncodedFlashPacket(Structure):
    def __init__(self):
        self.command = T_CommandPacketType.pt_WriteFlashEncoded.value
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("dataAddress", c_uint32),
        ("data", c_uint8 * UP_PAYLOAD_WITH_ADDRESS_SIZE)
    ]

class T_UpWriteDecodedFlashPacket(T_UpWriteEncodedFlashPacket):
    def __init__(self):
        super(T_UpWriteDecodedFlashPacket, self).__init__()
        self.command = T_CommandPacketType.pt_WriteFlashDecoded.value


class T_UpReadFlashCommandPacket(Structure):
    def __init__(self):
        super(T_UpReadFlashCommandPacket, self).__init__()
        self.command = T_CommandPacketType.pt_ReadFlash
        return
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("startingDataAddress", c_uint32),
        ("data", c_uint8 * UP_PAYLOAD_WITH_ADDRESS_SIZE)
    ]


class T_UpReadFlashPacket(T_UpWriteEncodedFlashPacket):
    def __init__(self, firmware_data):
        super(T_UpReadFlashPacket, self).__init__()
        self.command = int.from_bytes(firmware_data[:1], byteorder='little')
        if self.command != T_CommandPacketType.pt_ReadFlash.value:
            raise T_CommandPacketTypeException("Invalid command type")
        self.dataAddress = int.from_bytes(firmware_data[1:5], byteorder='little')
        dataPacketCBytes = (c_uint8 * UP_PAYLOAD_WITH_ADDRESS_SIZE).from_buffer_copy(firmware_data[5:UP_DATA_PACKET_SIZE])
        memmove(self.data, byref(dataPacketCBytes), UP_PAYLOAD_WITH_ADDRESS_SIZE)
        return


class T_UpAesInitFlashPacket(Structure):
    def __init__(self):
        super(T_UpAesInitFlashPacket, self).__init__()
        self.command = T_CommandPacketType.pt_AesReset.value
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("data", c_uint8 * UP_PAYLOAD_ONLY_COMMAND_SIZE)
    ]


class T_UpCrcRequestPacket(Structure):
    def __init__(self):
        super(T_UpCrcRequestPacket, self).__init__()
        self.command = T_CommandPacketType.pt_CheckCrc.value
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("startingDataAddress", c_uint32),
        ("endingDataAddress", c_uint32),
        ("data", c_uint8 * UP_PAYLOAD_WITH_TWO_ADDRESSES_SIZE)
    ]


class te_UpCrc32Status(Enum):
    bl_crc_Idle = 0
    bl_crc_Calculating = 1
    bl_crc_Calculated = 2


class T_UpCrcResponsePacket(Structure):
    def __init__(self, crc_data):
        super(T_UpCrcResponsePacket, self).__init__()
        self.command = int.from_bytes(crc_data[:1], byteorder='little')
        if self.command != T_CommandPacketType.pt_CheckCrc.value:
            raise T_CommandPacketTypeException("Invalid command type")
        self.startingDataAddress = int.from_bytes(crc_data[1:5], byteorder='little')
        self.endingDataAddress = int.from_bytes(crc_data[5:9], byteorder='little')
        self.crc_status = int.from_bytes(crc_data[9:10], byteorder='little')
        self.crc32_result = int.from_bytes(crc_data[10:14], byteorder='little')
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("startingDataAddress", c_uint32),
        ("endingDataAddress", c_uint32),
        ("crc_status", c_uint8),
        ("crc32_result", c_uint32),
        ("data", c_uint8 * (UP_PAYLOAD_WITH_TWO_ADDRESSES_SIZE - sizeof(c_uint8)))
    ]

BOOTLOADER_VECTOR_TABLE_ALIGNMENT = (0x100)
class tsBOOTLOADER_CRC_UNIT(Structure):
    _pack_ = 1
    _fields_ = [
        ("crc32_value", c_uint32),
        ("crc32_value_copy", c_uint32),
        ("startingAddress", c_uint32),
        ("endingAddress", c_uint32),
        ("data", c_uint8 * (BOOTLOADER_VECTOR_TABLE_ALIGNMENT - sizeof(c_uint32) * 4))
    ]

class T_UpLeaveBootloaderPacket(Structure):
    def __init__(self):
        super(T_UpLeaveBootloaderPacket, self).__init__()
        self.command = T_CommandPacketType.pt_LeaveBootloader.value
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("data", c_uint8 * UP_PAYLOAD_ONLY_COMMAND_SIZE)
    ]

class Te_WriteProtectionPacketType(Enum):
    bl_wrlp_NoProtection = 0
    bl_wrlp_LockAll = 1
    bl_wrlp_Unprotect = 2

    def __int__(self):
        return self.value

class Te_ReadProtectionPacketType(Enum):
    bl_rdlp_NoProtection = 0
    bl_rdlp_Protect_L1 = 1
    bl_rdlp_Protect_L2 = 2

    def __int__(self):
        return self.value

class T_UpLockDeviceRequestPacket(Structure):
    def __init__(self):
        super(T_UpLockDeviceRequestPacket, self).__init__()
        self.command = T_CommandPacketType.pt_Lock.value
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("writeProtection", c_uint8),
        ("readProtection", c_uint8),
        ("data", c_uint8 * (UP_DATA_LOCKPACKET_REQUEST_U8_DATA_SIZE))
    ]

class T_UpLockDeviceResponsePacket(Structure):
    def __init__(self, lock_packet_data):
        super(T_UpLockDeviceResponsePacket, self).__init__()
        self.command = int.from_bytes(lock_packet_data[:1], byteorder='little')
        if self.command != T_CommandPacketType.pt_Lock.value:
            raise T_CommandPacketTypeException("Invalid command type")
        self.readProtect = int.from_bytes(lock_packet_data[1:2], byteorder='little')
        self.OB_WRP_Sector_Info = int.from_bytes(lock_packet_data[2:6], byteorder='little')
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("readProtect", c_uint8),
        ("OB_WRP_Sector_Info", c_uint32),
        ("data", c_uint8 * UP_DATA_LOCKPACKET_RESPONSE_U8_DATA_SIZE)
    ]

class Te_ErrorPacketType(Enum):
    bl_err_Read_InvalidAddress = 0
    bl_err_WriteFlashError = 1
    bl_err_CheckCrc_Error = 2
    bl_err_MainProgramExecuted = 3
    bl_err_AccessDenied = 4

    def __int__(self):
        return self.value

class T_UpErrorPacket(Structure):
    def __init__(self, packet_data):
        super(T_UpErrorPacket, self).__init__()
        self.command = int.from_bytes(packet_data[:1], byteorder='little')
        if self.command != T_CommandPacketType.pt_ErrorState.value:
            raise T_CommandPacketTypeException("Invalid command type")
        self.commandWhichCausedTheError = int.from_bytes(packet_data[1:2], byteorder='little')
        self.error = int.from_bytes(packet_data[2:3], byteorder='little')
        return
    _pack_ = 1
    _fields_ = [
        ("command", c_uint8),
        ("commandWhichCausedTheError", c_uint8),
        ("error", c_uint8),
        ("data", c_uint8 * UP_DATA_PACKET_ERROR_DATA_SIZE)
    ]
