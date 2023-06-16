import ble_uart_v7rc
import bluetooth
import time
import math

ble_RAW_Data = None
ch1 = None
ch2 = None
ch3 = None
ch4 = None
ch1_x = None
ch2_y = None

def rx_callback():
  ble_RAW_Data = uart.read().decode().strip()
  ch1 = int((ble_RAW_Data[3:7]),10)
  ch2 = int((ble_RAW_Data[7:11]),10)
  ch3 = int((ble_RAW_Data[11:15]),10)
  ch4 = int((ble_RAW_Data[15:19]),10)
  ch1_x = ch1 - 1500
  ch2_y = ch2 - 1500
  print('BLE_RAW_DATA:')
  print(ble_RAW_Data)
  if math.fabs(ch1_x) == 0 and math.fabs(ch2_y) == 0:
    pass
  else:
    if math.fabs(ch1_x) > math.fabs(ch2_y):
      if ch1_x > 0:
        print('往右')
      else:
        print('往左')
    else:
      if ch2_y > 0:
        print('往前')
      else:
        print('往後')


ble = bluetooth.BLE()
uart = ble_uart_v7rc.ble_uart(ble, rx_callback=rx_callback, name="pico_ble")
