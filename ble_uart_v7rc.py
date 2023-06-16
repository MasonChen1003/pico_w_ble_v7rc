import bluetooth
from ble_advertising import advertising_payload
from ble_advertising import advertising_resp_payload
from micropython import const

_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),_FLAG_NOTIFY,)
_UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),_FLAG_WRITE,)
_UART_SERVICE = (_UART_UUID,(_UART_TX, _UART_RX),)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_CONNECTION_UPDATE = const(27)

# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)
_ADV_APPEARANCE_GENERIC_PHONE = const(64)

class ble_uart:
    def __init__(self, ble, rx_callback=None, name="ble-uart", rxbuf=100):
        self._ble = ble
        self._ble.active(True)
        self._ble.config(gap_name=name)  # add by Mason
        print("ble activated")

        self._write = self._ble.gatts_write
        self._read = self._ble.gatts_read
        self._notify = self._ble.gatts_notify

        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._handler = None
        self._ble.irq(self._irq)
        self._payload = advertising_payload(services=(_UART_UUID,),appearance=_ADV_APPEARANCE_GENERIC_PHONE)
        self._resp_payload = advertising_resp_payload(name=name)
        self._advertise()
        
        self._name = None
        self._addr_type = None
        self._addr = None
        self.irq(handler=rx_callback)

    def irq(self, handler):
        self._handler = handler

    def _irq(self, event, data): ## Bluetooth Interrupt Handler
       # print(event)
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr, = data
            self._connections.add(conn_handle)
            print("Connect")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
           # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle  = data
  #          if conn_handle in self._connections and value_handle == self._rx_handle:
            if conn_handle in self._connections:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                if self._handler:
                    self._handler()
        elif event == _IRQ_CONNECTION_UPDATE:          # Connection parameters were updated
        #    print(data)
            self.conn_handle, conn_interval, conn_latency, supervision_timeout, status = data
            print("Connection update")
        elif event == _IRQ_GATTS_READ_REQUEST:
            self.conn_handle, attr_handle = data
         #   print(data)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(None)  ##
        self._ble.gap_advertise(interval_us, adv_data=self._payload,resp_data=self._resp_payload)
        print("advertising...")

