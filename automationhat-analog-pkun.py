#!/usr/bin/env python3

import time

import automationhat
time.sleep(0.1) # short pause after ads1015 class creation recommended


print("""
Press CTRL+C to exit.
""")

# _numOfSteps = 12

#function rounding_to_step():
#   float divider = 5.0 / _numOfSteps
#   float selectorValueFloat = round(one / _divider)

while True:
    one = automationhat.analog.one.read()
    two = automationhat.analog.two.read()
    three = automationhat.analog.three.read()

    selectorValueFloatOne = round(one / (0.416666))
    selectorValueFloatTwo = round(two / (0.416666))
    selectorValueFloatThree = round(three / (0.416666))
    # print("1:")
    print("1: ", one, selectorValueFloatOne)
    print("2: ", two, selectorValueFloatTwo)
    print("3: ", three, selectorValueFloatThree)
    time.sleep(0.5)

