import collections
import logging
import threading
import struct

try:
    import can
    from can import Listener
    from can import CanError
except ImportError:
    # Do not fail if python-can is not installed
    can = None
    Listener = object
    CanError = Exception

from .node import RemoteNode, LocalNode
from .sync import SyncProducer
from .timestamp import TimeProducer
from .nmt import NmtMaster
from .lss import LssMaster
from .objectdictionary.eds import import_from_node

logger = logging.getLogger(__name__)


class Network(collections.MutableMapping):
    """Representation of one CAN bus containing one or more nodes."""

    def __init__(self, bus=None):
        """
        :param can.BusABC bus:
            A python-can bus instance to re-use.
        """
        #: A python-can :class:`can.BusABC` instance which is set after
        #: :meth:`canopen.Network.connect` is called
        self.bus = bus
        #: A :class:`~canopen.network.NodeScanner` for detecting nodes
        self.scanner = NodeScanner(self)
        #: List of :class:`can.Listener` objects.
        #: Includes at least MessageListener.
        self.listeners = [MessageListener(self)]
        self.notifier = None
        self.nodes = {}
        self.subscribers = {}
        self.send_lock = threading.Lock()
        self.sync = SyncProducer(self)
        self.time = TimeProducer(self)
        self.nmt = NmtMaster(0)
        self.nmt.network = self

        self.lss = LssMaster()
        self.lss.network = self
        self.subscribe(self.lss.LSS_RX_COBID, self.lss.on_message_received)

    def subscribe(self, can_id, callback):
        """Listen for messages with a specific CAN ID.

        :param int can_id:
            The CAN ID to listen for.
        :param callback:
            Function to call when message is received.
        """
        self.subscribers.setdefault(can_id, list())
        if callback not in self.subscribers[can_id]:
            self.subscribers[can_id].append(callback)

    def unsubscribe(self, can_id, callback=None):
        """Stop listening for message.

        :param int can_id:
            The CAN ID from which to unsubscribe.
        :param callback:
            If given, remove only this callback.  Otherwise all callbacks for
            the CAN ID.
        """
        if callback is None:
            del self.subscribers[can_id]
        else:
            self.subscribers[can_id].remove(callback)

    def connect(self, *args, **kwargs):
        """Connect to CAN bus using python-can.

        Arguments are passed directly to :class:`can.BusABC`. Typically these
        may include:

        :param channel:
            Backend specific channel for the CAN interface.
        :param str bustype:
            Name of the interface. See
            `python-can manual <https://python-can.readthedocs.io/en/latest/configuration.html#interface-names>`__
            for full list of supported interfaces.
        :param int bitrate:
            Bitrate in bit/s.

        :raises can.CanError:
            When connection fails.
        """
        # If bitrate has not been specified, try to find one node where bitrate
        # has been specified
        if "bitrate" not in kwargs:
            for node in self.nodes.values():
                if node.object_dictionary.bitrate:
                    kwargs["bitrate"] = node.object_dictionary.bitrate
                    break
        # Try to filter out only 11-bit IDs
        # kwargs.setdefault("can_filters",
        #                  [{"can_id": 0, "can_mask": 0x1FFFF800}])
        self.bus = can.interface.Bus(*args, **kwargs)
        logger.info("Connected to '%s'", self.bus.channel_info)
        self.notifier = can.Notifier(self.bus, self.listeners, 1)
        return self

    def disconnect(self):
        """Disconnect from the CAN bus.

        Must be overridden in a subclass if a custom interface is used.
        """
        for node in self.nodes.values():
            if hasattr(node, "pdo"):
                node.pdo.stop()
        self.notifier.stop()
        self.bus.shutdown()
        self.bus = None
        self.check()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def add_node(self, node, object_dictionary=None, upload_eds=False):
        """Add a remote node to the network.

        :param node:
            Can be either an integer representing the node ID, a
            :class:`canopen.RemoteNode` or :class:`canopen.LocalNode` object.
        :param object_dictionary:
            Can be either a string for specifying the path to an
            Object Dictionary file or a
            :class:`canopen.ObjectDictionary` object.
        :param bool upload_eds:
            Set ``True`` if EDS file should be uploaded from 0x1021.

        :return:
            The Node object that was added.
        :rtype: canopen.RemoteNode
        """
        if isinstance(node, int):
            if upload_eds:
                logger.info("Trying to read EDS from node %d", node)
                object_dictionary = import_from_node(node, self)
            node = RemoteNode(node, object_dictionary)
        self[node.id] = node
        return node

    def create_node(self, node, object_dictionary=None):
        """Create a local node in the network.

        :param node:
            An integer representing the node ID.
        :param object_dictionary:
            Can be either a string for specifying the path to an
            Object Dictionary file or a
            :class:`canopen.ObjectDictionary` object.

        :return:
            The Node object that was added.
        :rtype: canopen.LocalNode
        """
        if isinstance(node, int):
            node = LocalNode(node, object_dictionary)
        self[node.id] = node
        return node

    def send_message(self, can_id, data, remote=False):
        """Send a raw CAN message to the network.

        This method may be overridden in a subclass if you need to integrate
        this library with a custom backend.
        It is safe to call this from multiple threads.

        :param int can_id:
            CAN-ID of the message (always 11-bit)
        :param data:
            Data to be transmitted (anything that can be converted to bytes)
        :param bool remote:
            Set to True to send remote frame

        :raises can.CanError:
            When the message fails to be transmitted
        """
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")
        msg = can.Message(extended_id=False,
                          arbitration_id=can_id,
                          data=data,
                          is_remote_frame=remote)
        with self.send_lock:
            self.bus.send(msg)
        self.check()

    def read(self):
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")
        msg = self.bus.recv()
        return msg

    def send_periodic(self, can_id, data, period, remote=False):
        """Start sending a message periodically.

        :param int can_id:
            CAN-ID of the message (always 11-bit)
        :param data:
            Data to be transmitted (anything that can be converted to bytes)
        :param float period:
            Seconds between each message
        :param bool remote:
            indicates if the message frame is a remote request to the slave node

        :return:
            An task object with a ``.stop()`` method to stop the transmission
        :rtype: canopen.network.PeriodicMessageTask
        """
        return PeriodicMessageTask(can_id, data, period, self.bus, remote)

    def notify(self, can_id, data, timestamp):
        """Feed incoming message to this library.

        If a custom interface is used, this function must be called for each
        11-bit standard message read from the CAN bus.

        :param int can_id:
            CAN-ID of the message (always 11-bit)
        :param bytearray data:
            Data part of the message (0 - 8 bytes)
        :param float timestamp:
            Timestamp of the message, preferably as a Unix timestamp
        """
        if can_id in self.subscribers:
            callbacks = self.subscribers[can_id]
            for callback in callbacks:
                callback(can_id, data, timestamp)
        self.scanner.on_message_received(can_id)

    def check(self):
        """Check that no fatal error has occurred in the receiving thread.

        If an exception caused the thread to terminate, that exception will be
        raised.
        """
        exc = self.notifier.exception
        if exc is not None:
            logger.error("An error has caused receiving of messages to stop")
            raise exc

    def __getitem__(self, node_id):
        return self.nodes[node_id]

    def __setitem__(self, node_id, node):
        assert node_id == node.id
        self.nodes[node_id] = node
        node.associate_network(self)

    def __delitem__(self, node_id):
        self.nodes[node_id].remove_network()
        del self.nodes[node_id]

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)


class PeriodicMessageTask(object):
    """
    Task object to transmit a message periodically using python-can's
    CyclicSendTask
    """

    def __init__(self, can_id, data, period, bus, remote=False):
        """
        :param int can_id:
            CAN-ID of the message (always 11-bit)
        :param data:
            Data to be transmitted (anything that can be converted to bytes)
        :param float period:
            Seconds between each message
        :param can.BusABC bus:
            python-can bus to use for transmission
        """
        self.bus = bus
        self.period = period
        self.msg = can.Message(extended_id=False,
                               arbitration_id=can_id,
                               data=data, is_remote_frame=remote)
        self._task = None
        self._start()

    def _start(self):
        self._task = self.bus.send_periodic(self.msg, self.period)

    def stop(self):
        """Stop transmission"""
        self._task.stop()

    def update(self, data):
        """Update data of message

        :param data:
            New data to transmit
        """
        new_data = bytearray(data)
        old_data = self.msg.data
        self.msg.data = new_data
        if hasattr(self._task, "modify_data"):
            self._task.modify_data(self.msg)
        elif new_data != old_data:
            # Stop and start (will mess up period unfortunately)
            self._task.stop()
            self._start()


class MessageListener(Listener):
    """Listens for messages on CAN bus and feeds them to a Network instance.

    :param canopen.Network network:
        The network to notify on new messages.
    """

    def __init__(self, network):
        self.network = network

    def on_message_received(self, msg):
        if msg.is_error_frame or msg.is_remote_frame:
            return

        try:
            self.network.notify(msg.arbitration_id, msg.data, msg.timestamp)
        except Exception as e:
            # Exceptions in any callbaks should not affect CAN processing
            logger.error(str(e))


class NodeScanner(object):
    """Observes which nodes are present on the bus.

    Listens for the following messages:
     - Heartbeat (0x700)
     - SDO response (0x580)
     - TxPDO (0x180, 0x280, 0x380, 0x480)
     - EMCY (0x80)

    :param canopen.Network network:
        The network to use when doing active searching.
    """

    #: Activate or deactivate scanning
    active = True

    SERVICES = (0x700, 0x580, 0x180, 0x280, 0x380, 0x480, 0x80)

    def __init__(self, network=None):
        self.network = network
        #: A :class:`list` of nodes discovered
        self.nodes = []

    def on_message_received(self, can_id):
        service = can_id & 0x780
        node_id = can_id & 0x7F
        if node_id not in self.nodes and node_id != 0 and service in self.SERVICES:
            self.nodes.append(node_id)

    def reset(self):
        """Clear list of found nodes."""
        self.nodes = []

    def search(self, limit=127):
        """Search for nodes by sending SDO requests to all node IDs."""
        if self.network is None:
            raise RuntimeError("A Network is required to do active scanning")
        sdo_req = b"\x40\x00\x10\x00\x00\x00\x00\x00"
        for node_id in range(1, limit + 1):
            self.network.send_message(0x600 + node_id, sdo_req)

