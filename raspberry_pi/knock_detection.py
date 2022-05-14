# Python module to control the GPIO interface on the Raspberry Pi https://www.ics.com/blog/control-raspberry-pi-gpio-pins-python
import gpio_control as GPIO
import logging
import time
import os.path # for reading files

# get the knock pattern from the text file (storage)
# this function is defined before the variable declaration in order to be accessible
def get_knock_pattern():
    # check if the file exists
    if os.path.isfile('knock_pattern.txt'):
        # open the text file for reading
        with open('knock_pattern.txt', 'r') as input_file:
            # read the file
            knock_timings = input_file.read()
            # make a list of the values read from the file upon encountering the separator ','
            knock_pattern = knock_timings.split(',')
            # convert String type to int type
            knock_pattern = [int(knock_value) for knock_value in knock_pattern]
            return knock_pattern
    # if the file does not exist (first time run), create a new file with default knock pattern
    else:
        with open('knock_pattern.txt', 'w') as input_file:
            input_file.write('300,300')
            knock_pattern = [300, 300]
            return knock_pattern

# KNOCK PATTERN DETECTION VARIABLES
knock_pattern = get_knock_pattern() # list for storing the knock pattern, the default is 3 knocks every 300 milliseconds
threshhold = 190 # analog input value threshold
delay_before_knock = 0.2 # seconds
tolerance_total = 500 # milliseconds
tolerance_individual = 100 # milliseconds
max_knock_wait_time = 2000 # milliseconds
max_knock_pattern_recording_time = 10000 # milliseconds

# Configure logging
logger = logging.getLogger("Knock_Detection")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)



# get current time in milliseconds
def millis():
    return int(time.time()*1000)

# set the new knock pattern
def set_knock_pattern():
    # turn the RGB LED blue color on indicating the knock pattern setter mode
    GPIO.turn_on_LED_RGB('blue')
    logger.info("Starting setter")

    # initialize the variables of the setter
    received_first_knock = False
    waiting_finish = True
    knocks_received = []
    start = millis()
    previous_knock_time = 0
    current_knock_time = 0
    global knock_pattern

    # loop until the setter has finished
    while waiting_finish:
        # read the microphone analog input level
        sound_level = GPIO.read_analog()

        # check if the first knock is received
        if (sound_level > threshhold and received_first_knock == False):
            previous_knock_time = millis() # knock pattern starting time in millis
            received_first_knock = True
            GPIO.turn_on_LED_1_time(delay_before_knock) # turn on indicative LED that the knock was received with a delay
        
        # check if the second or further knock is received
        elif (sound_level > threshhold and received_first_knock == True):
            current_knock_time = millis() # current time in millis
            knocks_received.append(int(current_knock_time - previous_knock_time)) # store the time difference between the previous and the current knock
            previous_knock_time = current_knock_time # the last recorded knock is now the previous knock for the next knock
            GPIO.turn_on_LED_1_time(delay_before_knock) # turn on indicative LED that the knock was received with a delay

        # if the recording timed out and received less than 3 knocks, return False
        if (millis() - start > max_knock_pattern_recording_time and len(knocks_received) < 2):
             # change the LED RGB color depending on the door lock state in case it was unlocked from Alexa during the setting procedure
            if GPIO.is_door_unlocked_from_alexa():
                GPIO.turn_on_LED_RGB('green')
            else:
                GPIO.turn_on_LED_RGB('red')
                
            return False
        
        # elif the time out was reached while waiting for further knock and received at least 3 knocks, return True
        elif (millis() - previous_knock_time > max_knock_wait_time and len(knocks_received) >= 2):
            # update the permanent knock pattern variable
            knock_pattern = list(knocks_received)

            # update the permanent knock pattern file
            # open the text file using context manager for writing
            with open('knock_pattern.txt', 'w') as input_file:
                new_knock_pattern = ','.join(str(knock_timing) for knock_timing in knock_pattern) # convert the knock pattern list to a comma-separated string value, ex. "300,300,300"
                input_file.write(new_knock_pattern) # write the new value to the file overwriting the previous text

            # change the LED RGB color depending on the door lock state in case it was unlocked from Alexa during the setting procedure
            if GPIO.is_door_unlocked_from_alexa():
                GPIO.turn_on_LED_RGB('green')
            else:
                GPIO.turn_on_LED_RGB('red')
            
            return True

# validate the knock pattern to see if it is matching the set one
def validate_knock_pattern(start_time):
    logger.info("Starting validation")

    # turn on indicative LED that the knock was received with a delay
    # delay is needed here because the function is called right after detecting the first knock
    GPIO.turn_on_LED_1_time(delay_before_knock)

    # initialize the variables of the validator
    knocks_received = []
    waiting_finish = True
    received_second_knock = False
    previous_knock_time = start_time
    current_knock_time = 0

    while waiting_finish:
        # read the microphone analog input level
        sound_level = GPIO.read_analog()

        # second knock registered
        if (sound_level > threshhold):
            current_knock_time = millis() # knock pattern starting time in millis
            knocks_received.append(int(current_knock_time - previous_knock_time)) # store the time difference between the previous and the current knock
            # record if the second knock was ever received
            if (received_second_knock == False):
                received_second_knock = True
            previous_knock_time = current_knock_time # the last recorded knock is now the previous knock for the next knock
            
            GPIO.turn_on_LED_1_time(delay_before_knock) # turn on indicative LED that the knock was received with a delay

        # if no knock was received within the maximum waiting time, program assumes that the pattern was recorded and starts validation
        elif (millis() - previous_knock_time > max_knock_wait_time):
            passed = True

            # check if the recorded number of knocks matches the number of knocks in the set pattern
            if (len(knocks_received) != len(knock_pattern)):
                passed = False
                logger.info("Knock pattern invalid, received different number of knocks")
            
            # check if the knock recording time matches the total knock pattern time in the set pattern
            elif (abs(sum(knock_pattern) - sum(knocks_received)) > tolerance_total):
                passed = False
                logger.info("Knock pattern invalid, total knock incorrectness tolerance in millis exceeded")

            else:
                for i in range(len(knocks_received)):
                    if (abs(knocks_received[i] - knock_pattern[i]) > tolerance_individual):
                        passed = False
                        logger.info("Knock pattern invalid, individual knock incorrectness tolerance in millis exceeded")
                        break
            
            if (passed == True):
                logger.info("Knock pattern validated")

            logger.info("Knock pattern set:")
            logger.info(knock_pattern)
            logger.info("Knock pattern recorded now:")
            logger.info(knocks_received)

            return passed

def knock_detection():
    # while True:
    # NOT connected to ground (not active) and door is not unlocked from Alexa
    if GPIO.set_button_is_pressed() == False and GPIO.is_door_unlocked_from_alexa() == False:    
        if GPIO.unlock_button_is_pressed() == True:
            logger.info('Door unlock button pressed, unlocking door')
            GPIO.unlock_door_time(10)

        sound_level = GPIO.read_analog()

        if (sound_level > threshhold):
            start_time = millis()
            validated = validate_knock_pattern(start_time)
            if(validated):
                GPIO.unlock_door_time(10)
                
     # IS connected to ground (active) and door is not unlocked from Alexa
    elif GPIO.set_button_is_pressed() == True and GPIO.is_door_unlocked_from_alexa() == False:
        logger.info('Knock pattern setter button pressed, entering setter mode')
        if (set_knock_pattern()):
            logger.info("Knock pattern recorded successfully, pattern is:")
            logger.info(knock_pattern)
            GPIO.blink_LED_RGB(0.3, 'green')
        else:
            logger.info("Knock pattern not recorded, time exceeded without receiving at least 3 knocks")
            GPIO.blink_LED_RGB(0.3, 'red')

knock_detection()