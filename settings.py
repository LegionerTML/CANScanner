import configparser
import os


class Settings(object):
    def __init__(self, filename):
        self.__configChanged = False
        self.__configFileName = filename
        self.__display_values = dict()
        self.__display_values.update({"CANBaudrates": ("1000 kBit/s", "800 kBit/s", "500 kBit/s", "250 kBit/s", "125 kBit/s", "50 kBit/s", "20 kBit/s", "10 kBit/s")})
        #setting default values
        self.config = configparser.ConfigParser()
        self.config['CAN'] = {'BaudRate': '45'}
        self.config['CANOpen'] = {'NodeID': '6'}
        self.config['MCU_Memory_Volume'] = {"STM32F405RGT6": 0x00100000}
        if os.path.exists(filename) and os.access(os.path.dirname(filename), os.W_OK) and os.access(os.path.dirname(filename), os.R_OK):
            self.config.read(filename)
        elif not os.path.exists(filename) and os.access(os.path.dirname(filename), os.W_OK):
            with open(filename, 'w') as configfile:
                self.config.write(configfile)
        return

    def get(self, section, option):
        return self.config.get(section, option)

    def set(self, section, option, value):
        self.config.set(section, option, value)
        self.__configChanged = True
        return

    def getDisplayValue(self, key):
        return self.__display_values[key]

    def __del__(self):
        if self.__configChanged:
            with open(self.__configFileName, 'w') as configfile:  # save
                self.config.write(configfile)
        return
