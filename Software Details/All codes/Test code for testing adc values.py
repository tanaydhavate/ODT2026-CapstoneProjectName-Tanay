from machine import ADC, Pin
import time

adc = ADC(Pin(33))
adc.atten(ADC.ATTN_11DB)

while True:
    print(adc.read())   
    time.sleep(0.5)