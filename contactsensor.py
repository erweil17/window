#This program is for testing the window contact sensor.
#The red LED should light up whenever the sensor is making contact (or the window is closed)
from gpiozero import LED, Button
import time

led = LED(26)
window = Button(21)

while True:
    if window.is_pressed:
        led.on()
    else:
        led.off()
    time.sleep(0.1)
