# RGB LED class
# by Jian-You Lin


import sys
import os
import time

import board
import digitalio

class RGBLed:

    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        return

    # Turn on led
    def blink(self, pin=None):
        led = digitalio.DigitalInOut(pin)
        led.direction = digitalio.Direction.OUTPUT
        led.value = True

    # Turn off led
    def turn_off(self, pin=None):
        led = digitalio.DigitalInOut(pin)
        led.direction = digitalio.Direction.OUTPUT
        led.value = False
        
    def red_on(self):
        self.blink(self.red_pin)
    def red_off(self):
        self.turn_off(self.red_pin)
    
    def green_on(self):
        self.blink(self.green_pin)
    def green_off(self):
        self.turn_off(self.green_pin)
    
    def blue_on(self):
        self.blink(self.blue_pin)
    def blue_off(self):
        self.turn_off(self.blue_pin)

    def yellow_on(self):
        self.blink(self.red_pin)
        self.blink(self.green_pin)
    def yellow_off(self):
        self.turn_off(self.red_pin)
        self.turn_off(self.green_pin)
        
    def magenta_on(self):
        self.blink(self.red_pin)
        self.blink(self.blue_pin)
    def magenta_off(self):
        self.turn_off(self.red_pin)
        self.turn_off(self.blue_pin)

    def white_on(self):
        self.blink(self.red_pin)
        self.blink(self.green_pin)
        self.blink(self.blue_pin)
    def white_off(self):
        self.turn_off(self.red_pin)
        self.turn_off(self.green_pin)
        self.turn_off(self.blue_pin)
