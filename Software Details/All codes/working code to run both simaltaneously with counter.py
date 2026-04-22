import gc
gc.collect()

from time import sleep_ms
from machine import Pin, SPI, I2C, I2S
import os, sdcard, framebuf
from SH1106 import SH1106_I2C

cs = Pin(5, Pin.OUT)
cs.value(1)
sleep_ms(1000)
spi = SPI(1, baudrate=100000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
sleep_ms(500)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, "/sd")
print("SD OK")

frames = []
with open("/sd/gengar.bin", "rb") as f:
    while True:
        data = f.read(1024)
        if len(data) < 1024: break
        frames.append(bytearray(data))
print("Frames:", len(frames))
gc.collect()
print("Free RAM:", gc.mem_free())

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = SH1106_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.invert(True)
oled.show()

gc.collect()
audio = I2S(0, sck=Pin(26), ws=Pin(25), sd=Pin(27),
            mode=I2S.TX, bits=16, format=I2S.MONO,
            rate=8000, ibuf=4096)   # tiny ibuf - only 4KB

mono_buf = bytearray(512)   # small read chunks

def draw_info():
    oled.text("Gengar",     78,  0, 0)
    oled.text("----------", 70,  9, 0)
    oled.text("Ghost",      78, 18, 0)
    oled.text("Poison",     78, 27, 0)
    oled.text("----------", 70, 36, 0)
    oled.text("Kanto",      78, 45, 0)
    oled.text("1.5m 41kg",  70, 55, 0)

print("Playing...")
frame_i    = 0
loop_count = 0
wav = open("/sd/gengar.wav", "rb")
wav.seek(44)

while True:
    num = wav.readinto(mono_buf)
    if num == 0: break
    if num < 512:
        for i in range(num, 512): mono_buf[i] = 0

    audio.write(mono_buf)

    if loop_count % 6 == 0:   # update OLED every 6 loops
        fb = framebuf.FrameBuffer(
            frames[frame_i % len(frames)], 128, 64, framebuf.MONO_HLSB)
        oled.fill(1)
        oled.blit(fb, 0, 0)
        draw_info()
        oled.show()
        frame_i += 1

    loop_count += 1

wav.close()
audio.deinit()
print("Done!")
