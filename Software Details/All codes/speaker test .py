import gc
gc.collect()

from machine import Pin, I2S
import math, array
from time import sleep_ms

audio = I2S(0, sck=Pin(26), ws=Pin(25), sd=Pin(27),
            mode=I2S.TX, bits=16, format=I2S.MONO,
            rate=8000, ibuf=4096)


buf = array.array('h', [0] * 256)
for i in range(256):
    buf[i] = int(30000 * math.sin(2 * math.pi * i * 440 / 8000))

raw = bytes(buf)
print("Playing tone for 5 seconds...")
for _ in range(400):
    audio.write(raw)

audio.deinit()
print("Done")
