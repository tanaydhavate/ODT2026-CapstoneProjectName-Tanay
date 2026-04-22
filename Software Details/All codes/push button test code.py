from machine import Pin
from time import sleep_ms

BOOT_BTN_PIN = 34
SCAN_BTN_PIN = 35

boot_btn = Pin(BOOT_BTN_PIN, Pin.IN)
scan_btn = Pin(SCAN_BTN_PIN, Pin.IN)

print("Button test running...")
print("Press BOOT (GPIO 34) or SCAN (GPIO 35)")
print("---")

while True:
    boot = boot_btn.value()
    scan = scan_btn.value()

    if boot == 0:
        print("BOOT pressed  | GPIO 34 = 0")
    else:
        print("BOOT idle     | GPIO 34 = 1")

    if scan == 0:
        print("SCAN pressed  | GPIO 35 = 0")
    else:
        print("SCAN idle     | GPIO 35 = 1")

    sleep_ms(300)


    sleep_ms(100)
