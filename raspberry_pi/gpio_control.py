# Python module to control the GPIO interface on the Raspberry Pi https://www.ics.com/blog/control-raspberry-pi-gpio-pins-python

import RPi.GPIO as GPIO
import logging
import smbus
import time

# SMBUS SETUP
bus = smbus.SMBus(1) # initialize the SMBus object (I2C bus)  for reading the data from A/D converter
ADDRESS = 0x48 # address to of reading the data from A/D converter
ANALOG_CHN = 3 # analog input pin of the A/D converter

# GPIO PINS (BCM, not board pin)
BTN_SET_PIN = 22 # GPIO setter mode button input
BTN_UNLOCK_PIN = 24 # GPIO door unlock button input 
SOLENOID_PIN = 23 # GPIO LED output
LED_KNOCK_PIN = 12 # GPIO LED output
LED_B_PIN = 16 # GPIO LED RGB Blue output
LED_G_PIN = 20 # GPIO LED RGB Green output
LED_R_PIN = 21 # GPIO LED RGB Red output

# STATE INFORMATION
door_unlocked_from_alexa = False

# GPIO SETUP
# use BCM channel (GPIO) numbering for pins instead of physical board pins
GPIO.setmode(GPIO.BCM)
# Setter mode button input
GPIO.setup(BTN_SET_PIN, GPIO.IN, GPIO.PUD_UP)
# Door unlock button input
GPIO.setup(BTN_UNLOCK_PIN, GPIO.IN, GPIO.PUD_UP)
# Solenoid output
GPIO.setup(SOLENOID_PIN, GPIO.OUT)
GPIO.output(SOLENOID_PIN, GPIO.LOW)
# LED 1 output (knock detection)
GPIO.setup(LED_KNOCK_PIN, GPIO.OUT)
GPIO.output(LED_KNOCK_PIN, GPIO.LOW)
# LED RGB output (blue=programming, green=unlocked, red=locked)
# On startup the door is locked, so the RED color pin is set to HIGH
GPIO.setup(LED_B_PIN, GPIO.OUT)
GPIO.output(LED_B_PIN, GPIO.LOW)
GPIO.setup(LED_G_PIN, GPIO.OUT)
GPIO.output(LED_G_PIN, GPIO.LOW)
GPIO.setup(LED_R_PIN, GPIO.OUT)
GPIO.output(LED_R_PIN, GPIO.HIGH)

# Configure logging
logger = logging.getLogger("GPIO_Control")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# read the analog value from A/D converter
def read_analog():
    return bus.read_byte_data(ADDRESS, ANALOG_CHN)

# check if the setter mode button is pressed
def set_button_is_pressed():
    if GPIO.input(BTN_SET_PIN):
        return False
    else:
        return True

# check if the unlock button is pressed
def unlock_button_is_pressed():
    if GPIO.input(BTN_UNLOCK_PIN):
        return False
    else:
        return True

# unlock the door for the specified time in seconds, this will automatically handle the status LED color
def unlock_door_time(delay_time):
    logger.info('Unlocking door for {} seconds'.format(delay_time))
    global door_unlocked_from_alexa
    turn_on_LED_RGB('green')
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)

    time.sleep(delay_time)

    logger.info('Locking the door')
    
    if door_unlocked_from_alexa == False:
        turn_on_LED_RGB('red')
        GPIO.output(SOLENOID_PIN, GPIO.LOW)

# unlock the door, this will automatically handle the status LED color
def unlock_door():
    global door_unlocked_from_alexa
    door_unlocked_from_alexa = True
    turn_on_LED_RGB('green')
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)
    logger.info('Door unlocked from Alexa')

# lock the door, this will automatically handle the status LED color
def lock_door():
    global door_unlocked_from_alexa
    door_unlocked_from_alexa = False
    turn_on_LED_RGB('red')
    GPIO.output(SOLENOID_PIN, GPIO.LOW)
    logger.info('Door locked from Alexa')

def is_door_unlocked_from_alexa():
    return door_unlocked_from_alexa

# turn on the LED Knock Detection for the specified time in seconds
# redundant analog reads help to avoid false duplicate knock detections
def turn_on_LED_1_time(delay_time):
    GPIO.output(LED_KNOCK_PIN, GPIO.HIGH)
    read_analog()
    time.sleep(delay_time)
    read_analog()
    GPIO.output(LED_KNOCK_PIN, GPIO.LOW)

# turn on the LED Knock Detection 
def turn_on_LED_1():
    GPIO.output(LED_KNOCK_PIN, GPIO.HIGH)

# turn off the LED Knock Detection 
def turn_off_LED_1():
    GPIO.output(LED_KNOCK_PIN, GPIO.LOW)

# turn on a particular LED RGB color
def turn_on_LED_RGB(color):
    if color == 'blue':
        GPIO.output(LED_G_PIN, GPIO.LOW)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        GPIO.output(LED_B_PIN, GPIO.HIGH)
    elif color == 'green':
        GPIO.output(LED_B_PIN, GPIO.LOW)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        GPIO.output(LED_G_PIN, GPIO.HIGH)
    elif color == 'red':
        GPIO.output(LED_B_PIN, GPIO.LOW)
        GPIO.output(LED_G_PIN, GPIO.LOW)
        GPIO.output(LED_R_PIN, GPIO.HIGH)
    else:
        logger.error('The LED RGB color requested is invalid, expected blue, green, red, received {}}'.format(color))
        return

# blink the selected RGB LED color 3 times with selected time intervals in seconds
def blink_LED_RGB(delay_time, color):
    if color == 'green':
        GPIO.output(LED_B_PIN, GPIO.LOW)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        GPIO.output(LED_G_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_G_PIN, GPIO.LOW)
    elif color == 'red':
        GPIO.output(LED_B_PIN, GPIO.LOW)
        GPIO.output(LED_G_PIN, GPIO.LOW)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.LOW)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.HIGH)
        time.sleep(delay_time)
        GPIO.output(LED_R_PIN, GPIO.LOW)
    else:
        logger.error('The LED RGB color requested is invalid, expected green or red, received {}}'.format(color))
        return
    
    GPIO.output(LED_R_PIN, GPIO.HIGH)