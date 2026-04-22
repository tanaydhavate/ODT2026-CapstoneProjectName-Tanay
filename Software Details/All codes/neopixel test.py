from machine import Pin
from neopixel import NeoPixel
from time import sleep

NUM_LEDS = 8     
PIN_NUM = 4      

np = NeoPixel(Pin(PIN_NUM, Pin.OUT), NUM_LEDS)

def show_color(r, g, b):
    for i in range(NUM_LEDS):
        np[i] = (r, g, b)
    np.write()

while True:
    show_color(255, 0, 0)   
    sleep(1)
    show_color(0, 255, 0)   
    sleep(1)
    show_color(0, 0, 255)  
    sleep(1)
    show_color(0, 0, 0)    
    sleep(1)
