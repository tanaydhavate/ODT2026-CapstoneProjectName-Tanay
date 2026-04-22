import machine, sys
from time import sleep_ms

if hasattr(sys, '_soft_reset'):
    machine.reset()

from machine import Pin, SPI, I2S
import os, sdcard

cs = Pin(5, Pin.OUT)
cs.value(1)
sleep_ms(1000)
spi = SPI(1, baudrate=100000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
sleep_ms(500)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, "/sd")
print("SD OK")

# I2S init AFTER SD
audio = I2S(0, sck=Pin(26), ws=Pin(25), sd=Pin(27),
            mode=I2S.TX, bits=16, format=I2S.STEREO,
            rate=8000, ibuf=20000)

mono   = bytearray(512)
stereo = bytearray(1024)

print("Playing...")
f = open("/sd/gengar.wav", "rb")
f.seek(44)

while True:
    num = f.readinto(mono)
    if num == 0: break
    if num < 512:
        for i in range(num, 512): mono[i] = 0
    i = 0
    j = 0
    while i < 512:
        stereo[j]   = mono[i]
        stereo[j+1] = mono[i+1]
        stereo[j+2] = mono[i]
        stereo[j+3] = mono[i+1]
        i += 2
        j += 4
    audio.write(stereo)

f.close()
audio.deinit()
print("Done")
