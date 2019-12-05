"""
Communicates with :ref:`cpp_lib32 <cpp-lib>` via the :class:`~.cpp32.Cpp32` class.

Example of a module that can be executed within a 64-bit Python interpreter which can
communicate with a 32-bit library, :ref:`cpp_lib32 <cpp-lib>`, that is hosted
by a 32-bit Python server, :mod:`.cpp32`. A 64-bit process cannot load a
32-bit library and therefore `inter-process communication <ipc_>`_ is used to
interact with a 32-bit library from a 64-bit process.

:class:`~.cpp64.Cpp64` is the 64-bit client and :class:`~.cpp32.Cpp32`
is the 32-bit server for `inter-process communication <ipc_>`_.

.. _ipc: https://en.wikipedia.org/wiki/Inter-process_communication
"""
import os

from msl.loadlib import Client64


class sieca132_client(Client64):
    """Communicates with a 32-bit C++ library, :ref:`cpp_lib32 <cpp-lib>`.

    This class demonstrates how to communicate with a 32-bit C++ library if an
    instance of this class is created within a 64-bit Python interpreter.
    """

    def __init__(self):
        # specify the name of the corresponding 32-bit server module, cpp32, which hosts
        # the 32-bit C++ library -- cpp_lib32.
        super(sieca132_client, self).__init__(module32='sieca132_server_x32', append_sys_path=os.path.dirname(__file__))
    def canStatus(self, handle):
        return self.request32('canStatus', handle)

    def canGetDllInfo(self):
        return self.request32('canGetDllInfo')

    def canIdAdd(self, handle, l_id):
        return self.request32('canIdAdd', handle, l_id)

    def canOpen(self, l_netnumber, l_mode, l_echoon, l_txtimeout, l_rxtimeout, c_Applicationname, c_ReceiverEvent, c_ErrorEvent):
        return self.request32('canOpen', l_netnumber, l_mode, l_echoon, l_txtimeout, l_rxtimeout, c_Applicationname, c_ReceiverEvent, c_ErrorEvent)

    def canClose(self, handle):
        return self.request32('canClose', handle)

    def canSetBaudrate(self, handle, l_baud):
        return self.request32('canSetBaudrate', handle, l_baud)

    def canBlinkLED(self, handle, ulMode, ulStatus, ulPattern):
        return self.request32('canBlinkLED', handle, ulMode, ulStatus, ulPattern)

    def canIsNetOwner(self, handle):
        return self.request32('canIsNetOwner', handle)

    def canSetFilterMode(self, handle, t_mode):
        return self.request32('canSetFilterMode', handle, t_mode)

    def canRead(self, handle):
        return self.request32('canRead', handle)

    def canReadNoWait(self, handle):
        return self.request32('canReadNoWait', handle)

    def canConfirmedTransmit(self, handle, cmsg, l_len):
        return self.request32('canConfirmedTransmit', handle, cmsg, l_len)

    def canSend(self, handle, cmsg, l_len):
        return self.request32('canSend', handle, cmsg, l_len)

    def canWrite(self, handle, cmsg, l_len):
        return self.canSend(handle, cmsg, l_len)
