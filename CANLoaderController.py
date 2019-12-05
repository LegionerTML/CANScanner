from __future__ import absolute_import
import canopen
import time
import os
from time import sleep
from CANTypeDefs import T_CANOPEN_OD_INDEX, T_CANOPEN_PROGRAM_INDEX, T_CANOPEN_PROGRAM_STATE, T_UpPacket, T_CommandPacketTypeException, \
    T_UpWriteEncodedFlashPacket, T_UpReadFlashCommandPacket, T_UpReadFlashPacket, T_UpWriteDecodedFlashPacket, T_UpAesInitFlashPacket, \
    T_CommandPacketType, T_UpCrcRequestPacket, te_UpCrc32Status, T_UpCrcResponsePacket, T_UpLeaveBootloaderPacket, T_UpErrorPacket, \
    Te_ErrorPacketType, T_UpLockDeviceRequestPacket, T_UpLockDeviceResponsePacket, Te_WriteProtectionPacketType, Te_ReadProtectionPacketType, UP_PAYLOAD_WITH_ADDRESS_SIZE, \
     tsBOOTLOADER_CRC_UNIT
from Types_STM32F405 import Te_OB_WRP_Sector
from CANFoxLib import CANFoxLibSkin, CANfoxHardwareException
from ctypes import *
from Crc32 import crc32
import settings
import queue

FLASH_BASE = 0x08000000
BOOTLOADER_ADDRESS = FLASH_BASE
BOOTLOADER_SIZE = 0x8000
BOOTLOADER_CRC_UNIT_SIZE = (sizeof(tsBOOTLOADER_CRC_UNIT))
BOOTLOADER_CRC_UNIT_ADDRESS = FLASH_BASE + BOOTLOADER_SIZE
APPLICATION_ADDRESS = (BOOTLOADER_CRC_UNIT_ADDRESS + BOOTLOADER_CRC_UNIT_SIZE)

BOOTLOADER_CRC32_CHECK_ATTEMPTS = 30
BOOTLOADER_CRC32_CHECK_TIMEOUT = 0.3
BOOTLOADER_TIME_BETWEEN_PROGRAMS_SWITCHING = 0.3
BOOTLOADER_LOCK_WRITE_UNLOCK_TIMEOUT = 0.5
BOOTLOADER_LOCK_WRITE_UNLOCK_ATTEMPTS = 15
BOOTLOADER_WRITE_FIRMWARE_DATA__АFTER_HOW_MANY_PACKETS_CHECK_ERRORS = 30


class CANLoaderCommunicationException(Exception):
    pass


class CANLoaderDeviceFailureException(Exception):
    pass


class CANLoaderPacketSequenceException(Exception):
    pass


class CANLoaderFirmwareVerifyException(Exception):
    pass


class CANLoaderFirmwareProgrammingException(Exception):
    pass

def raise_(ex):
    raise ex


class CANLoaderController(object):
    def __init__(self, settings):
        self.can_network = canopen.Network()
        self.can_network.connect(channel=159, bustype='canfox', settings=settings)
        self.reprogrammable_devices = None
        self.settings = settings

    def can_reader(self):
        msg1 = self.can_network.read()
        return msg1
        #RxMessage = self.can_network.listeners.on_message_received(msg)

    def discover_connected_devices(self):
        self.can_network.scanner.reset()
        self.can_network.scanner.search()
        time.sleep(0.05)
        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        rel_path_master = r"master_dictionary.eds" #self dictionary
        rel_path_remote = r"object_dictionary.eds"
        abs_file_path_master_eds = os.path.join(script_dir, rel_path_master)
        abs_file_path_remote_eds = os.path.join(script_dir, rel_path_remote)
        local_node_id = int(self.settings.get("CANOpen", "NodeID"))
        localnode = canopen.LocalNode(local_node_id, abs_file_path_master_eds)
        self.can_network.add_node(localnode)
        for node_id in self.can_network.scanner.nodes:
            self.can_network.add_node(node_id, abs_file_path_remote_eds)
        return self.can_network.scanner.nodes

    def find_reprogrammable_devices(self):
        remote_reprogrammable_devices = dict()
        remote_reprogrammable_devices_iterator = 0
        #sort devices
        online_nodes = dict(sorted(self.can_network.nodes.items()))

        for node_id, value in self.can_network.nodes.items():
            if value.__class__.__name__ != "LocalNode":
                try:
                    data = value.sdo.upload(T_CANOPEN_OD_INDEX.DeviceType.value, 0)
                    #check for DS401 profile conformity (0x1000h Device type = 0x00%%0191h
                    device_type = int.from_bytes(data[:2], byteorder='little', signed=False)
                    if device_type == 0x191:
                        # check dor identity object (0x1018 Identity)
                        number_of_entries = value.sdo.upload(T_CANOPEN_OD_INDEX.Identity.value, 0)
                        number_of_different_programms_supported_on_the_node = value.sdo.upload(
                            T_CANOPEN_OD_INDEX.DownloadProgramData.value, 0)
                        if number_of_entries[0] == 4 and number_of_different_programms_supported_on_the_node[0] == 2:
                            value._bag_ = dict()
                            value.sdo.upload(T_CANOPEN_OD_INDEX.Identity.value, 1)
                            vendor_id = value.sdo.upload(T_CANOPEN_OD_INDEX.Identity.value, 1)
                            vendor_id = int.from_bytes(vendor_id, byteorder='little', signed=False)
                            serial_number = value.sdo.upload(T_CANOPEN_OD_INDEX.Identity.value, 4)
                            serial_number = int.from_bytes(serial_number, byteorder='little', signed=False)
                            manufacturer_device_name = value.sdo.upload(T_CANOPEN_OD_INDEX.ManufacturerDeviceName.value, 0)
                            value._bag_['Vendor Id (0x1018_1)'] = hex(vendor_id)
                            value._bag_['Serial number (0x1018_4)'] = serial_number
                            value._bag_['Manufacturer device name (0x1008_0)'] = manufacturer_device_name.decode()
                            if vendor_id == 0x77777777:
                                remote_reprogrammable_devices[remote_reprogrammable_devices_iterator] = value
                                remote_reprogrammable_devices_iterator += 1
                except canopen.sdo.exceptions.SdoCommunicationError:
                    pass
            self.reprogrammable_devices = remote_reprogrammable_devices
        return remote_reprogrammable_devices

    def __reset_aes(self, device):
        packet_reset_aes = T_UpAesInitFlashPacket()
        device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                    T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                    bytes(packet_reset_aes))

    def reset_lock_state(self, reprogrammable_device_index):
        device = self.reprogrammable_devices[reprogrammable_device_index]
        #0. Getting lock state from remote mcu
        packet_check_lock = T_UpLockDeviceRequestPacket()
        packet_check_lock.writeProtection = Te_WriteProtectionPacketType.bl_wrlp_NoProtection.value
        packet_check_lock.readProtection = Te_ReadProtectionPacketType.bl_rdlp_NoProtection.value
        device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                    T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                    bytes(packet_check_lock))
        packet_lock_from_mcu = device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                         T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
        lock_data = T_UpLockDeviceResponsePacket(packet_lock_from_mcu)
        if lock_data.readProtect == Te_ReadProtectionPacketType.bl_rdlp_Protect_L2.value:
            raise CANLoaderDeviceFailureException("Device read-protected level 2. Cannot update firmware. Forever. Goodbye!")
        for sector in Te_OB_WRP_Sector:
            if sector.value & lock_data.OB_WRP_Sector_Info == 0 and sector != Te_OB_WRP_Sector.OB_WRP_Sector_0.value and sector != Te_OB_WRP_Sector.OB_WRP_Sector_1.value:    #only firmware sectors
                packet_check_lock.writeProtection = Te_WriteProtectionPacketType.bl_wrlp_Unprotect
                device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                    T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                    bytes(packet_check_lock))
                for attempt in range(BOOTLOADER_LOCK_WRITE_UNLOCK_ATTEMPTS):
                    sleep(BOOTLOADER_LOCK_WRITE_UNLOCK_TIMEOUT) #device need time to reboot and apply settings
                    try:
                        packet_lock_from_mcu = device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                         T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                    except canopen.sdo.exceptions.SdoCommunicationError:
                        pass
                    else:
                        break
                lock_data = T_UpLockDeviceResponsePacket(packet_lock_from_mcu)

                #check for lock data for firmware sectors is in non-locked state
                if (lock_data.OB_WRP_Sector_Info & (Te_OB_WRP_Sector.OB_WRP_Sector_0.value | Te_OB_WRP_Sector.OB_WRP_Sector_1.value)) != 0:
                    raise CANLoaderDeviceFailureException("Device cannot reset Write-protect Option Byte")
                break
            sleep(0.2)
        return



    def upload_firmware_file(self, reprogrammable_device_index, filename, progressQueue, serviceQueue):
        current_device = self.reprogrammable_devices[reprogrammable_device_index]
        with open(filename.get(), "rb") as file:
            firmware_data = file.read()
        if len(firmware_data) <= 0 or len(firmware_data) % 4 != 0:
            progressQueue.put(100)
            return
        try:
            # reset_aes - must be a first packet, because it erases cleared sectors table
            self.__reset_aes(current_device)
            #       #calc crc32 summ and starting, ending addresses for firmware and appending to firmware
            # crc_summ = crc32(firmware_data)
            firmware_data_byteorder_big = bytearray()
            for uint32 in range(int(len(firmware_data) / 4)):
                firmware_data_byteorder_big += firmware_data[uint32 * 4:uint32 * 4 + 4][::-1]
            crc_summ = crc32(firmware_data_byteorder_big)
            starting_address = APPLICATION_ADDRESS
            ending_address = APPLICATION_ADDRESS + len(firmware_data) - 1
            #checking for maximum address
            flash_volume_in_bytes = int(self.settings.get("MCU_Memory_Volume", current_device._bag_['Manufacturer device name (0x1008_0)']))
            if ending_address >= starting_address + flash_volume_in_bytes:
                raise CANLoaderFirmwareProgrammingException("Invalid firmware size. Firmware end address: {0}, MCU end address: {1}".format(str(ending_address), str(starting_address + flash_volume_in_bytes)))
            crc32_data = crc_summ.to_bytes(4, byteorder="little") + crc_summ.to_bytes(4, byteorder="little") +\
                         starting_address.to_bytes(4, byteorder="little") + ending_address.to_bytes(4, byteorder="little")
            packet = T_UpWriteDecodedFlashPacket()
            dataPacketCBytes = (c_uint8 * UP_PAYLOAD_WITH_ADDRESS_SIZE).from_buffer_copy(
                crc32_data)
            memmove(packet.data, byref(dataPacketCBytes), UP_PAYLOAD_WITH_ADDRESS_SIZE)
            packet.dataAddress = BOOTLOADER_CRC_UNIT_ADDRESS
            current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                        T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                        bytes(packet))

            # preparing for software download
            current_data_section = 0
            packetIterator = 0
            while current_data_section < len(firmware_data):
                try:
                    if serviceQueue.qsize() > 0:
                        service_message = serviceQueue.get(0)
                        if service_message == "exit":
                            return
                except queue.Empty:
                    pass  # no data
                # creating WritePacket
                current_address = APPLICATION_ADDRESS + current_data_section
                packet = T_UpWriteEncodedFlashPacket()
                packet.dataAddress = current_address
                packetLength = UP_PAYLOAD_WITH_ADDRESS_SIZE if len(
                    firmware_data) - current_data_section >= UP_PAYLOAD_WITH_ADDRESS_SIZE else len(
                    firmware_data) - current_data_section
                dataPacketCBytes = (c_uint8 * packetLength).from_buffer_copy(
                    firmware_data[current_data_section:current_data_section + packetLength])
                memmove(packet.data, byref(dataPacketCBytes), packetLength)
                # creating of buffer to send data
                current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                            T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                            bytes(packet))
                current_data_section += UP_PAYLOAD_WITH_ADDRESS_SIZE
                packetIterator += 1
                if packetIterator % 10 == 0:
                    progressQueue.put(100 * current_data_section / len(firmware_data))
                #check for errors
                if packetIterator % BOOTLOADER_WRITE_FIRMWARE_DATA__АFTER_HOW_MANY_PACKETS_CHECK_ERRORS == 0:
                    packet_from_mcu = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                                T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                    try:
                        error_packet = T_UpErrorPacket(packet_from_mcu)
                    except T_CommandPacketTypeException:
                        pass
                    else:
                        if error_packet.commandWhichCausedTheError != T_CommandPacketType.pt_WriteFlashEncoded.value:
                            pass
                        {
                            Te_ErrorPacketType.bl_err_WriteFlashError: lambda: raise_(CANLoaderFirmwareProgrammingException("Write flash error.")),
                            Te_ErrorPacketType.bl_err_CheckCrc_Error: lambda: None,
                            Te_ErrorPacketType.bl_err_MainProgramExecuted: lambda: raise_(CANLoaderFirmwareProgrammingException("Main program executed?")),
                            Te_ErrorPacketType.bl_err_AccessDenied: lambda: lambda: raise_(CANLoaderFirmwareProgrammingException("Reading from bootloader area is impossible."))
                        }[error_packet.error]()


            # checking crc32
            crc_request_packet = T_UpCrcRequestPacket()
            crc_request_packet.startingDataAddress = starting_address
            crc_request_packet.endingDataAddress = ending_address
            current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                        T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                        bytes(crc_request_packet))

            for i in range(BOOTLOADER_CRC32_CHECK_ATTEMPTS):
                sleep(BOOTLOADER_CRC32_CHECK_TIMEOUT)
                packet_from_mcu = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                            T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                print(tuple(packet_from_mcu))
                crc_packet = T_UpCrcResponsePacket(packet_from_mcu)
                if crc_packet.crc_status == te_UpCrc32Status.bl_crc_Calculated.value:
                    if crc_summ == crc_packet.crc32_result:
                        break
                    else:
                        raise CANLoaderFirmwareVerifyException("Invalid CRC32 summ")
            else:
                raise CANLoaderFirmwareVerifyException("Remote MCU cannot calculate CRC32 summ")

        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        return

    def verify_firmware_file(self, reprogrammable_device_index, filename, progressQueue, serviceQueue):
        current_device = self.reprogrammable_devices[reprogrammable_device_index]
        with open(filename.get(), "rb") as file:
            firmware_data_to_check = file.read()

        try:
            # reset_aes - must be a first packet, because it erases cleared sectors table
            self.__reset_aes(current_device)
            packet_initial_read = T_UpReadFlashCommandPacket()
            packet_initial_read.startingDataAddress = APPLICATION_ADDRESS
            current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                        T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                        bytes(packet_initial_read))
            # continuous reading...
            current_data_section = 0
            packetIterator = 0
            while current_data_section < len(firmware_data_to_check):
                try:
                    if serviceQueue.qsize() > 0:
                        service_message = serviceQueue.get(0)
                        if service_message == "exit":
                            return
                except queue.Empty:
                    pass  # no data
                packet_from_mcu = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                            T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                part_firmware_data_in_mcu = packet_from_mcu[-UP_PAYLOAD_WITH_ADDRESS_SIZE:]
                part_firmware_data_to_check = firmware_data_to_check[
                                              current_data_section:current_data_section + UP_PAYLOAD_WITH_ADDRESS_SIZE]
                if len(part_firmware_data_in_mcu) > len(part_firmware_data_to_check):
                    part_firmware_data_in_mcu = part_firmware_data_in_mcu[:len(part_firmware_data_to_check)]
                if part_firmware_data_to_check == part_firmware_data_in_mcu:
                    pass
                else:
                    raise CANLoaderFirmwareVerifyException("Invalid data")
                current_data_section += UP_PAYLOAD_WITH_ADDRESS_SIZE
                packetIterator += 1
                if packetIterator >= 10:
                    packetIterator = 0
                    progressQueue.put(100 * current_data_section / len(firmware_data_to_check))

        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        return

        pass
    def download_firmware_file(self, reprogrammable_device_index, filename, progressQueue,
                                                      serviceQueue):
        current_device = self.reprogrammable_devices[reprogrammable_device_index]
        #flash_volume_in_bytes = MCU_Memory_Volume[current_device._bag_['Manufacturer device name (0x1008_0)']]
        flash_volume_in_bytes = int(self.settings.get("MCU_Memory_Volume", current_device._bag_['Manufacturer device name (0x1008_0)']))
        end_address = FLASH_BASE + flash_volume_in_bytes - 1
        starting_address = APPLICATION_ADDRESS
        firmware_size = (end_address - starting_address)
        packetIterator = 0
        try:
            # reset_aes - must be a first packet, because it erases cleared sectors table
            self.__reset_aes(current_device)
            #creating ReadPacket command
            packet = T_UpReadFlashCommandPacket()
            packet.startingDataAddress = starting_address
            packetLength = UP_PAYLOAD_WITH_ADDRESS_SIZE
            dataPacketCBytes = (c_uint8 * packetLength).from_buffer_copy(bytearray(UP_PAYLOAD_WITH_ADDRESS_SIZE))
            memmove(packet.data, byref(dataPacketCBytes), packetLength)
            #creating of buffer to send data
            current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                    T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                    bytes(packet))
            firmware_data = bytearray()
            current_data_section_from_programmer = 0
            while starting_address + current_data_section_from_programmer < end_address:
                try:
                    if serviceQueue.qsize() > 0:
                        service_message = serviceQueue.get(0)
                        if service_message == "exit":
                            return
                except queue.Empty:
                    pass  # no data
                data_from_MCU = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                          T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                try:
                    packet_from_MCU = T_UpReadFlashPacket(data_from_MCU)
                    firmware_data += bytes(packet_from_MCU.data)
                    current_address = starting_address + current_data_section_from_programmer
                    if packet_from_MCU.dataAddress != current_address:
                        raise CANLoaderPacketSequenceException("Invalid data address")
                except T_CommandPacketTypeException as e:
                    pass
                packetIterator += 1
                if packetIterator >= 10:
                    packetIterator = 0
                    progressQueue.put(100*current_data_section_from_programmer/firmware_size)
                current_data_section_from_programmer += UP_PAYLOAD_WITH_ADDRESS_SIZE
            firmware_file = open(filename, 'w+b')
            firmware_file.write(firmware_data)
            firmware_file.close()

        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        except Exception as e:
            raise CANLoaderDeviceFailureException(str(e))
        return
    def mcu_leave_bootloader(self, reprogrammable_device_index):
        try:
            current_device = self.reprogrammable_devices[reprogrammable_device_index]
            is_bootloader_running = current_device.sdo.upload(T_CANOPEN_OD_INDEX.ProgramControl.value, T_CANOPEN_PROGRAM_INDEX.Bootloader.value)
            is_bootloader_running = int.from_bytes(is_bootloader_running, byteorder='little', signed=False)
            if is_bootloader_running == T_CANOPEN_PROGRAM_STATE.Started.value:
                current_device.sdo.download(T_CANOPEN_OD_INDEX.ProgramControl.value,
                                            T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                            str(chr(T_CANOPEN_PROGRAM_STATE.LaunchCommandSent.value)).encode())
                sleep(BOOTLOADER_TIME_BETWEEN_PROGRAMS_SWITCHING)
                is_main_program_running = current_device.sdo.upload(T_CANOPEN_OD_INDEX.ProgramControl.value,
                                                                  T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                is_main_program_running = int.from_bytes(is_main_program_running, byteorder='little', signed=False)
                if is_main_program_running != T_CANOPEN_PROGRAM_STATE.Started.value:
                    packet_from_mcu = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                                                T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                    try:
                        packet = T_UpErrorPacket(packet_from_mcu)
                        if packet.commandWhichCausedTheError == T_CommandPacketType.pt_LeaveBootloader.value:
                            raise CANLoaderFirmwareProgrammingException("MainProgram start failure " + str(Te_ErrorPacketType(packet.error)))
                    except T_CommandPacketTypeException as e:
                        pass
                    raise CANLoaderFirmwareProgrammingException("MainProgram start failure. Device cannot execute.")
            else:
                #all ok, in main program
                pass

        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        except CANfoxHardwareException:
            pass
        except Exception as e:
            raise CANLoaderFirmwareProgrammingException(str(e))
        return
    def move_mcu_to_bootloader(self, reprogrammable_device_index):
        current_device = self.reprogrammable_devices[reprogrammable_device_index]

        try:
            #check for device already in bootloader
            is_bootloader_running = current_device.sdo.upload(T_CANOPEN_OD_INDEX.ProgramControl.value, T_CANOPEN_PROGRAM_INDEX.Bootloader.value)
            is_bootloader_running = int.from_bytes(is_bootloader_running, byteorder='little', signed=False)

            if is_bootloader_running == T_CANOPEN_PROGRAM_STATE.Started.value:
                #all ok, in bootloader now
                pass
            else:
                current_device.sdo.download(T_CANOPEN_OD_INDEX.ProgramControl.value,
                                            T_CANOPEN_PROGRAM_INDEX.Bootloader.value,
                                            str(chr(T_CANOPEN_PROGRAM_STATE.LaunchCommandSent.value)).encode())
                sleep(BOOTLOADER_TIME_BETWEEN_PROGRAMS_SWITCHING)
                is_bootloader_running = current_device.sdo.upload(T_CANOPEN_OD_INDEX.ProgramControl.value, T_CANOPEN_PROGRAM_INDEX.Bootloader.value)
                is_bootloader_running = int.from_bytes(is_bootloader_running, byteorder='little', signed=False)
                if is_bootloader_running != T_CANOPEN_PROGRAM_STATE.Started.value:
                    raise CANLoaderDeviceFailureException("Bootloader start failure")

        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        except CANfoxHardwareException:
            pass
        except Exception as e:
            raise CANLoaderDeviceFailureException(str(e))
        return

    def mcu_lock(self, reprogrammable_device_index):
        current_device = self.reprogrammable_devices[reprogrammable_device_index]
        try:
            packet_lock_device = T_UpLockDeviceRequestPacket()
            packet_lock_device.command = T_CommandPacketType.pt_Lock.value
            packet_lock_device.writeProtection = Te_WriteProtectionPacketType.bl_wrlp_LockAll.value
            packet_lock_device.readProtection = Te_ReadProtectionPacketType.bl_rdlp_Protect_L1.value
            current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                        T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                        bytes(packet_lock_device))
            isLockValid = False
            for i in range(BOOTLOADER_LOCK_WRITE_UNLOCK_ATTEMPTS):
                try:
                    sleep(BOOTLOADER_LOCK_WRITE_UNLOCK_TIMEOUT)
                    packet_lock_device.writeProtection = Te_WriteProtectionPacketType.bl_wrlp_NoProtection.value
                    packet_lock_device.readProtection = Te_ReadProtectionPacketType.bl_rdlp_NoProtection.value
                    current_device.sdo.download(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                            T_CANOPEN_PROGRAM_INDEX.MainProgram.value,
                                            bytes(packet_lock_device))
                    lock_state_from_mcu = current_device.sdo.upload(T_CANOPEN_OD_INDEX.DownloadProgramData.value,
                                    T_CANOPEN_PROGRAM_INDEX.MainProgram.value)
                except canopen.sdo.exceptions.SdoCommunicationError:
                    pass
                else:
                    try:
                        lock_packet = T_UpLockDeviceResponsePacket(lock_state_from_mcu)
                    except T_CommandPacketTypeException:
                        pass
                    else:
                        if lock_packet.readProtect == Te_ReadProtectionPacketType.bl_rdlp_Protect_L1.value and lock_packet.OB_WRP_Sector_Info == 0:
                            isLockValid = True
                            break
            if isLockValid == False:
                raise CANLoaderDeviceFailureException("Device did not send correct answer")
        except canopen.sdo.exceptions.SdoCommunicationError:
            self.can_network.bus.canfoxAdapter.hardware_is_available()
        except CANfoxHardwareException:
            pass
        except Exception as e:
            raise CANLoaderDeviceFailureException(str(e))
        return

    def __del__(self):
        if self.can_network.scanner.network.bus !=None:
            self.can_network.disconnect()

