from machine import Pin, I2C
from time import sleep_ms

sleep_ms(500)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
print("Scan:", i2c.scan())