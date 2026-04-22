import gc
import os
import sdcard
import framebuf

from time import sleep_ms, sleep, ticks_ms, ticks_diff
from machine import Pin, SPI, I2C, I2S, ADC, reset
from neopixel import NeoPixel
from SH1106 import SH1106_I2C

gc.collect()

# ─── Pin Constants ─────────────────────────────────────────────────────────────
SD_CS_PIN    = 5
SD_SCK_PIN   = 18
SD_MOSI_PIN  = 23
SD_MISO_PIN  = 19

NEOPIXEL_PIN = 4
NUM_LEDS     = 16

OLED_SCL_PIN = 22
OLED_SDA_PIN = 21
OLED_ADDR    = 0x3C
OLED_W       = 128
OLED_H       = 64

I2S_SCK_PIN  = 26
I2S_WS_PIN   = 25
I2S_SD_PIN   = 27

ADC_PIN      = 33
BOOT_BTN_PIN = 34
SCAN_BTN_PIN = 35

# ─── Timing / Audio Constants ──────────────────────────────────────────────────
FRAME_WIDTH    = 128
FRAME_HEIGHT   = 64
FRAME_SIZE     = 1024
AUDIO_RATE     = 8000
AUDIO_BUF_SIZE = 8192
MONO_BUF_SIZE  = 512
LONG_PRESS_MS  = 2000
ADC_SAMPLES    = 20


# ══════════════════════════════════════════════════════════════════════════════
# HARDWARE INIT
# ══════════════════════════════════════════════════════════════════════════════

def init_sd():
    cs = Pin(SD_CS_PIN, Pin.OUT)
    cs.value(1)
    sleep_ms(300)
    spi = SPI(1, baudrate=100000, polarity=0, phase=0,
              sck=Pin(SD_SCK_PIN), mosi=Pin(SD_MOSI_PIN), miso=Pin(SD_MISO_PIN))
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

def init_oled():
    i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
    oled = SH1106_I2C(OLED_W, OLED_H, i2c, addr=OLED_ADDR)
    oled.fill(0)
    oled.show()
    return i2c, oled

def init_audio():
    return I2S(0, sck=Pin(I2S_SCK_PIN), ws=Pin(I2S_WS_PIN), sd=Pin(I2S_SD_PIN),
               mode=I2S.TX, bits=16, format=I2S.MONO,
               rate=AUDIO_RATE, ibuf=AUDIO_BUF_SIZE)

def init_adc():
    adc = ADC(Pin(ADC_PIN))
    adc.atten(ADC.ATTN_11DB)
    return adc

def init_buttons():
    boot_btn = Pin(BOOT_BTN_PIN, Pin.IN)
    scan_btn = Pin(SCAN_BTN_PIN, Pin.IN)
    return boot_btn, scan_btn


# ══════════════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def strip_clear(strip):
    strip.fill((0, 0, 0))
    strip.write()

def oled_message(oled, line1, line2="", line3=""):
    oled.fill(0)
    oled.invert(False)
    if line1: oled.text(line1, max(0, (128 - len(line1) * 8) // 2), 16)
    if line2: oled.text(line2, max(0, (128 - len(line2) * 8) // 2), 30)
    if line3: oled.text(line3, max(0, (128 - len(line3) * 8) // 2), 44)
    oled.show()

def load_frames(path):
    frames = []
    with open(path, "rb") as f:
        while len(frames) < 30:
            data = f.read(FRAME_SIZE)
            if len(data) < FRAME_SIZE:
                break
            frames.append(bytearray(data))
    return frames

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
            size = chunk[4] | (chunk[5]<<8) | (chunk[6]<<16) | (chunk[7]<<24)
            f.seek(size, 1)
    return f

def play_audio_with_animation(oled, frames, wav_path, draw_fn):
    audio = None
    wav   = None
    try:
        audio    = init_audio()
        mono_buf = bytearray(MONO_BUF_SIZE)
        wav      = open_wav(wav_path)
        frame_i  = 0
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
                draw_fn(oled, frames[frame_i % len(frames)])
                frame_i += 1
            loop_count += 1
    finally:
        if wav:   wav.close()
        if audio: audio.deinit()

def read_adc_average(adc):
    total = 0
    for _ in range(ADC_SAMPLES):
        total += adc.read()
        sleep_ms(25)
    return total // ADC_SAMPLES

def check_long_press(boot_btn):
    if boot_btn.value() == 0:
        t = ticks_ms()
        while boot_btn.value() == 0:
            if ticks_diff(ticks_ms(), t) >= LONG_PRESS_MS:
                return True
            sleep_ms(50)
    return False

def wait_for_button_release(btn):
    while btn.value() == 0:
        sleep_ms(20)


# ══════════════════════════════════════════════════════════════════════════════
# BOOT ANIMATION — Y G R pattern fills all 16 LEDs, then wipes back off
# ══════════════════════════════════════════════════════════════════════════════

BOOT_COLORS = [
    (150, 120, 0),
    (0,   150, 0),
    (150, 0,   0),
] * 6   # 18 values, use first 16

def boot_animation(oled, strip):
    oled_message(oled, "POKEDEX", "Booting...")
    strip_clear(strip)
    for i in range(NUM_LEDS):
        strip[i] = BOOT_COLORS[i]
        strip.write()
        sleep_ms(80)
    sleep_ms(600)
    for i in range(NUM_LEDS - 1, -1, -1):
        strip[i] = (0, 0, 0)
        strip.write()
        sleep_ms(40)
    strip_clear(strip)

def scan_animation(strip):
    strip_clear(strip)
    for i in range(NUM_LEDS):
        strip[i] = (0, 80, 0)
        strip.write()
        sleep_ms(50)


# ══════════════════════════════════════════════════════════════════════════════
# POKEMON FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

# ── SNIVY  |  510Ω  |  ADC 70–80  ─────────────────────────────────────────────
def snivy_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Snivy",      66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Grass",      66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Unova",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.6m 8.1kg", 66, 55, 1)
    oled.show()

def play_snivy(oled, strip):
    print("Snivy!")
    for i in range(8):           strip[i] = (0, 120, 0)
    for i in range(8, NUM_LEDS): strip[i] = (0, 60, 0)
    strip.write()
    frames = load_frames("/sd/snivy.bin")
    if not frames: oled_message(oled, "Snivy", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/snivy.wav", snivy_draw_frame)


# ── VAPOREON  |  510+330Ω  |  ADC 160–190  ────────────────────────────────────
def vaporeon_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Vaporeon",   66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Water",      66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Kanto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("1.0m 29kg",  66, 55, 1)
    oled.show()

def play_vaporeon(oled, strip):
    print("Vaporeon!")
    for i in range(8):           strip[i] = (0, 80, 150)
    for i in range(8, NUM_LEDS): strip[i] = (0, 40, 80)
    strip.write()
    frames = load_frames("/sd/vaporeon.bin")
    if not frames: oled_message(oled, "Vaporeon", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/vaporeon.wav", vaporeon_draw_frame)


# ── RAICHU  |  1kΩ  |  ADC 230–245  ───────────────────────────────────────────
def raichu_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Raichu",     66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Electric",   66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Kanto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.8m 30kg",  66, 55, 1)
    oled.show()

def play_raichu(oled, strip):
    print("Raichu!")
    for i in range(8):           strip[i] = (150, 100, 0)
    for i in range(8, NUM_LEDS): strip[i] = (80, 50, 0)
    strip.write()
    frames = load_frames("/sd/raichu.bin")
    if not frames: oled_message(oled, "Raichu", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/raichu.wav", raichu_draw_frame)


# ── UMBREON  |  1kΩ+510Ω  |  ADC 380–420  ────────────────────────────────────
def umbreon_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Umbreon",    66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Dark",       66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Johto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("1.0m 27kg",  66, 55, 1)
    oled.show()

def play_umbreon(oled, strip):
    print("Umbreon!")
    for i in range(8):           strip[i] = (100, 0, 0)
    for i in range(8, NUM_LEDS): strip[i] = (50, 0, 0)
    strip.write()
    frames = load_frames("/sd/umbreon.bin")
    if not frames: oled_message(oled, "Umbreon", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/umbreon.wav", umbreon_draw_frame)


# ── PIKACHU  |  2kΩ  |  ADC 510–550  ──────────────────────────────────────────
def pikachu_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Pikachu",    66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Electric",   66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Kanto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.4m 6kg",   66, 55, 1)
    oled.show()

def play_pikachu(oled, strip):
    print("Pikachu!")
    for i in range(8):           strip[i] = (150, 150, 0)
    for i in range(8, NUM_LEDS): strip[i] = (80, 80, 0)
    strip.write()
    frames = load_frames("/sd/pikachu.bin")
    if not frames: oled_message(oled, "Pikachu", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/pikachu.wav", pikachu_draw_frame)


# ── MUDKIP  |  2kΩ+510Ω  |  ADC 640–690  ─────────────────────────────────────
def mudkip_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Mudkip",     66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Water",      66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Hoenn",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.4m 7.6kg", 66, 55, 1)
    oled.show()

def play_mudkip(oled, strip):
    print("Mudkip!")
    for i in range(8):           strip[i] = (0, 0, 139)
    for i in range(8, NUM_LEDS): strip[i] = (0, 0, 70)
    strip.write()
    frames = load_frames("/sd/mudkip.bin")
    if not frames: oled_message(oled, "Mudkip", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/mudkip.wav", mudkip_draw_frame)


# ── MEW  |  3kΩ  |  ADC 750–800  ─────────────────────────────────────────────
def mew_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Mew",        66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Psychic",    66, 18, 1)
    oled.text("----------", 66, 27, 1)
    oled.text("Kanto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.4m 4kg",   66, 55, 1)
    oled.show()

def play_mew(oled, strip):
    print("Mew!")
    for i in range(8):           strip[i] = (180, 100, 150)
    for i in range(8, NUM_LEDS): strip[i] = (90, 50, 80)
    strip.write()
    frames = load_frames("/sd/mew.bin")
    if not frames: oled_message(oled, "Mew", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/mew.wav", mew_draw_frame)


# ── JIGGLYPUFF  |  3kΩ+510Ω  |  ADC 870–910  ─────────────────────────────────
def jigglypuff_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Jigglypuf",  66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Normal",     66, 18, 1)
    oled.text("Fairy",      66, 27, 1)
    oled.text("Kanto",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.5m 5.5kg", 66, 55, 1)
    oled.show()

def play_jigglypuff(oled, strip):
    print("Jigglypuff!")
    for i in range(4): strip[i] = (255, 255, 255)
    for i in range(4,8): strip[i] = (255, 20, 147)
    strip.write()
    frames = load_frames("/sd/jigglypuff.bin")
    if not frames: oled_message(oled, "Jigglypuf", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/jigglypuff.wav", jigglypuff_draw_frame)


# ── GENGAR  |  4kΩ  |  ADC 980–1010  ─────────────────────────────────────────
def gengar_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(1)
    oled.invert(True)
    oled.blit(fb, 0, 0)
    oled.text("Gengar",     78,  0, 0)
    oled.text("----------", 70,  9, 0)
    oled.text("Ghost",      78, 18, 0)
    oled.text("Poison",     78, 27, 0)
    oled.text("----------", 70, 36, 0)
    oled.text("Kanto",      78, 45, 0)
    oled.text("1.5m 41kg",  70, 55, 0)
    oled.show()

def play_gengar(oled, strip):
    print("Gengar!")
    for i in range(4):           strip[i] = (75, 0, 180)
    for i in range(4, 8): strip[i] = (250, 0, 250)
    strip.write()
    frames = load_frames("/sd/gengar.bin")
    if not frames: oled_message(oled, "Gengar", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/gengar.wav", gengar_draw_frame)


# ── SPHEAL  |  4kΩ+510Ω  |  ADC 1080–1110  ───────────────────────────────────
def spheal_draw_frame(oled, frame_bytes):
    fb = framebuf.FrameBuffer(frame_bytes, FRAME_WIDTH, FRAME_HEIGHT, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.invert(False)
    oled.blit(fb, 0, 0)
    oled.fill_rect(64, 0, 64, 64, 0)
    oled.text("Spheal",     66,  0, 1)
    oled.text("----------", 66,  9, 1)
    oled.text("Ice",        66, 18, 1)
    oled.text("Water",      66, 27, 1)
    oled.text("Hoenn",      66, 36, 1)
    oled.text("----------", 66, 45, 1)
    oled.text("0.8m 39.5k", 66, 55, 1)
    oled.show()

def play_spheal(oled, strip):
    print("Spheal!")
    for i in range(4):           strip[i] = (0, 150, 200)
    for i in range(4,8 ): strip[i] = (0, 0, 250)
    strip.write()
    frames = load_frames("/sd/spheal.bin")
    if not frames: oled_message(oled, "Spheal", "No frames!"); sleep(2); return
    gc.collect()
    play_audio_with_animation(oled, frames, "/sd/spheal.wav", spheal_draw_frame)


# ══════════════════════════════════════════════════════════════════════════════
# ADC IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def identify_and_play(adc_val, oled, strip):
    if   50  <= adc_val <= 80:    play_snivy(oled, strip)
    elif 160 <= adc_val <= 190:   play_vaporeon(oled, strip)
    elif 210 <= adc_val <= 245:   play_raichu(oled, strip)
    elif 380 <= adc_val <= 420:   play_umbreon(oled, strip)
    elif 510 <= adc_val <= 550:   play_pikachu(oled, strip)
    elif 640 <= adc_val <= 690:   play_mudkip(oled, strip)
    elif 750 <= adc_val <= 800:   play_mew(oled, strip)
    elif 870 <= adc_val <= 910:   play_jigglypuff(oled, strip)
    elif 980 <= adc_val <= 1010:  play_gengar(oled, strip)
    elif 1080 <= adc_val <= 1110: play_spheal(oled, strip)
    else:
        oled_message(oled, "Unknown", "ADC:" + str(adc_val), "Try again")
        strip_clear(strip)
        sleep(2)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN STATE MACHINE
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("Pokedex standby — waiting for BOOT press")

    spi, sd            = init_sd()
    strip              = init_neopixel()
    i2c, oled          = init_oled()
    adc                = init_adc()
    boot_btn, scan_btn = init_buttons()

    # ── STANDBY — everything off until BOOT pressed ───────────────────────────
    while boot_btn.value() == 1:
        sleep_ms(50)

    wait_for_button_release(boot_btn)

    # ── BOOT ANIMATION ────────────────────────────────────────────────────────
    boot_animation(oled, strip)

    # ── MAIN LOOP ─────────────────────────────────────────────────────────────
    while True:

        oled_message(oled, "POKEDEX", "Ready to Scan", "Press SCAN")
        strip_clear(strip)

        # Wait for SCAN press | long-press BOOT = reboot
        while True:
            if check_long_press(boot_btn):
                oled_message(oled, "Rebooting...")
                strip_clear(strip)
                sleep(1)
                reset()
            if scan_btn.value() == 0:
                sleep_ms(50)
                wait_for_button_release(scan_btn)
                break

        # Scanning
        oled_message(oled, "Scanning...")
        scan_animation(strip)

        adc_val = read_adc_average(adc)
        print("ADC avg:", adc_val)

        oled_message(oled, "Scanning...", "ADC:" + str(adc_val))
        sleep_ms(500)

        identify_and_play(adc_val, oled, strip)

        strip_clear(strip)
        oled_message(oled, "Ready to", "Catch!", "Press SCAN")
        sleep(2)
        gc.collect()


try:
    main()
except Exception as e:
    print("FATAL:", e)
