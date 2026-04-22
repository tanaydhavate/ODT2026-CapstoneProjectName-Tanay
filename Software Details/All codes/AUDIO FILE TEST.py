from machine import Pin, SPI
import os, sdcard

cs = Pin(5, Pin.OUT)
spi = SPI(1, baudrate=400000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
sd = sdcard.SDCard(spi, cs)
os.mount(sd, "/sd")

f = open("/sd/gengar.wav", "rb")
h = f.read(44)
f.close()

print("RIFF:", h[0:4])
print("WAVE:", h[8:12])
print("Format:", h[20] | h[21]<<8)
print("Channels:", h[22] | h[23]<<8)
print("Rate:", h[24] | h[25]<<8 | h[26]<<16 | h[27]<<24)
print("Bits:", h[34] | h[35]<<8)
print("DataChunk:", h[36:40])
print("DataSize:", h[40] | h[41]<<8 | h[42]<<16 | h[43]<<24)
