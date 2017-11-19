from Adafruit_AMG88xx import Adafruit_AMG88xx, AMG88xx_ABSOLUTE_VALUE
from gpiozero import Button

# connect the INT (interupt) pin to GPIO 17
interupt = Button(17)
sensor = Adafruit_AMG88xx()

sensor.setInterruptLevels(30, 50, 50 * .95)
sensor.setInterruptMode(AMG88xx_ABSOLUTE_VALUE)
sensor.enableInterrupt()

interupt.wait_for_press()

print("interupted")

print(sensor.getInterrupt())

sensor.disableInterrupt()
