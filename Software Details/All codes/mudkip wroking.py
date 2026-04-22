import gc
import os
import sdcard
import framebuf

from time import sleep_ms
from machine import Pin, SPI, I2C, I2S
from neopixel import NeoPixel
from SH1106 import SH1106_I2C

gc.collect()

SD_CS_PIN       = 5
SD_SCK_PIN      = 18
SD_MOSI_PIN     = 23
SD_MISO_PIN     = 19

NEOPIXEL_PIN    = 4
NUM_LEDS        = 8

OLED_SCL_PIN    = 22
OLED_SDA_PIN    = 21
OLED_ADDR       = 0x3C
OLED_W          = 128
OLED_H          = 64

I2S_SCK_PIN     = 26
I2S_WS_PIN      = 25
I2S_SD_PIN      = 27

FRAME_WIDTH     = 128
FRAME_HEIGHT    = 64
FRAME_SIZE      = 1024

AUDIO_RATE      = 8000
AUDIO_BUF_SIZE  = 8192
MONO_BUF_SIZE   = 512

FRAME_FILE      = "/sd/mudkip.bin"
WAV_FILE        = "/sd/mudkip.wav"

DARK_BLUE       = (0, 0, 139)


def init_sd():
    cs = Pin(SD_CS_PIN, Pin.OUT)
    cs.value(1)
    sleep_ms(300)
    spi = SPI(
        1,
        baudrate=100000,
        polarity=0,
        phase=0,
        sck=Pin(SD_SCK_PIN),
        mosi=Pin(SD_MOSI_PIN),
        miso=Pin(SD_MISO_PIN)
    )
    sleep_ms(200)
    sd = sdcard.SDCard(spi, cs)
    os.mount(sd, "/sd")
    print("SD OK")
    return spi, sd

def init_neopixel():
    pin = Pin(NEOPIXEL_PIN, Pin.OUT, value=0)
    strip = NeoPixel(pin, NUM_LEDS)
    strip.fill((0, 0, 0))
    strip.write()
    sleep_ms(50)
    return strip

def show_mudkip_colors(strip):
    for i in range(8):
        strip[i] = DARK_BLUE

    strip.write()

def clear_strip(strip):
    strip.fill((0, 0, 0))
    strip.write()

def load_frames(path):
    frames = []
    with open(path, "rb") as f:
        while True:
            data = f.read(FRAME_SIZE)
            if len(data) < FRAME_SIZE:
                break
            frames.append(bytearray(data))
    return frames

def init_oled():
    i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
    oled = SH1106_I2C(OLED_W, OLED_H, i2c, addr=OLED_ADDR)
    oled.fill(0)
    oled.show()
    return i2c, oled

def draw_info(oled):
    oled.text("Mudkip",     66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Water",      66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Hoenn",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.4m 7.6kg", 66, 55, 1)

def draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    draw_info(oled)
    oled.show()

def init_audio():
    return I2S(
        0,
        sck=Pin(I2S_SCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=AUDIO_RATE,
        ibuf=AUDIO_BUF_SIZE
    )

def open_wav(path):
    f = open(path, "rb")
    f.seek(0)
    header = f.read(44)
    if header[36:40] != b'data':
        while True:
            chunk = f.read(8)
            if not chunk or len(chunk) < 8:
                break
            if chunk[:4] == b'data':
                break
            size = chunk[4] + (chunk[5]<<8) + (chunk[6]<<16) + (chunk[7]<<24)
            f.seek(size, 1)
    return f

spi = None
sd = None
np = None
oled = None
audio = None
wav = None

try:
    spi, sd = init_sd()

    np = init_neopixel()
    show_mudkip_colors(np)

    frames = load_frames(FRAME_FILE)
    print("Frames:", len(frames))

    gc.collect()
    print("Free RAM:", gc.mem_free())

    if len(frames) == 0:
        raise Exception("No frames found in mudkip.bin")

    i2c, oled = init_oled()

    gc.collect()
    sleep_ms(500)
    audio = init_audio()
    mono_buf = bytearray(MONO_BUF_SIZE)

    wav = open_wav(WAV_FILE)
    print("WAV open, playing Mudkip...")

    frame_i = 0
    loop_count = 0

    while True:
        num = wav.readinto(mono_buf)
        if num == 0:
            break

        if num < MONO_BUF_SIZE:
            for i in range(num, MONO_BUF_SIZE):
                mono_buf[i] = 0

        audio.write(mono_buf)

        if loop_count % 6 == 0:
            draw_frame(oled, frames[frame_i % len(frames)])
            frame_i += 1

        loop_count += 1

    print("Playback done")

except Exception as e:
    print("ERROR:", e)

finally:
    try:
        if wav:
            wav.close()
    except:
        pass

    try:
        if audio:
            audio.deinit()
    except:
        pass

    try:
        if np:
            clear_strip(np)
            sleep_ms(50)
    except:
        pass

    try:
        if oled:
            oled.fill(0)
            oled.show()
    except:
        pass

    gc.collect()
    print("Mudkip complete!")
