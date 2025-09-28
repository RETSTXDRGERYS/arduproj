# ble_simple_peripheral.py
import bluetooth
import struct
from micropython import const

_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX   = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
              bluetooth.FLAG_NOTIFY,)
_UART_RX   = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
              bluetooth.FLAG_WRITE,)

_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX,),)

class BLESimplePeripheral:
    def __init__(self, ble, name="PicoESC"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx, self._rx,),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._advertise(name)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            if attr_handle == self._rx:
                msg = self._ble.gatts_read(self._rx)
                if self._write_callback:
                    self._write_callback(msg)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx, data.encode())

    def is_connected(self):
        return len(self._connections) > 0

    def read(self):
        return self._ble.gatts_read(self._rx)

    def on_write(self, callback):
        self._write_callback = callback

    def _advertise(self, name="PicoESC"):
        self._ble.gap_advertise(100, bytearray(
            b"\x02\x01\x06"
            + bytes((len(name) + 1, 0x09))
            + name.encode()
        ))
