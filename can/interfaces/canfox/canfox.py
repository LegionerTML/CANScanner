# coding: utf-8

"""
Enable basic CAN over a PCAN USB device.
"""

import logging
import sys
import time

import can
from CANFoxLib import CANFoxLibSkin
from can import CanError, Message, BusABC
from can.bus import BusState


class CANFoxBus(BusABC):

    def __init__(self, channel=159, state=BusState.ACTIVE, bitrate=500000, *args, **kwargs):
        self.canfoxAdapter = CANFoxLibSkin(*args, **kwargs)

        """A PCAN USB interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the PCAN interface includes the :meth:`~can.interface.pcan.PcanBus.flash`
        and :meth:`~can.interface.pcan.PcanBus.status` methods.

        :param str channel:
            The can interface name. An example would be 'PCAN_USBBUS1'
            Default is 'PCAN_USBBUS1'

        :param can.bus.BusState state:
            BusState of the channel.
            Default is ACTIVE

        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 kbit/s.

        """
        self.channel_info = channel
        
        super(CANFoxBus, self).__init__(channel=channel, state=state, bitrate=bitrate, *args, **kwargs)



    def reset(self):
        pass

    def _recv_internal(self, timeout):
        Msg = self.canfoxAdapter.recv_async()

        return Msg, False

    def send(self, msg, timeout=None):
        self.canfoxAdapter.send(msg,timeout)
        pass


    def shutdown(self):
        self.canfoxAdapter.shutdown()
		
    @property
    def state(self):
        pass

    @state.setter
    def state(self, new_state):
        pass
