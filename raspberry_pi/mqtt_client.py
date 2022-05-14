from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient # documentation available at https://s3.amazonaws.com/aws-iot-device-sdk-python-docs/sphinx/html/index.html#module-AWSIoTPythonSDK.MQTTLib
import gpio_control as GPIO
import time
import logging
import json
import os
from dotenv import load_dotenv # can be installed using "pip install python-dotenv" in the terminal

import knock_detection

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# load environmental variables from the .env file
load_dotenv()

# assign environmental variables
host = os.environ.get('AWS_IOT_ENDPOINT') # AWS IoT endpoint
port = os.environ.get("AWS_IOT_PORT") # MQTT non-WebSocket port
clientId = os.environ.get("AWS_IOT_CLIENTID")
thingName = os.environ.get("AWS_IOT_THINGNAME") # name of the IoT thing in AWS
rootCA = os.environ.get("AWS_IOT_ROOT_CA")
private_key = os.environ.get("AWS_IOT_PRIVATE_KEY")
certificate = os.environ.get("AWS_IOT_CERT")

update_topic = "$aws/things/{0}/shadow/update".format(thingName) # update topic
update_documents_topic = "$aws/things/{0}/shadow/update/documents".format(thingName) # update documents topic

# AWSIoTMQTTClient default configuration
mqttClient = AWSIoTMQTTClient(clientId)
mqttClient.configureEndpoint(host, port)
mqttClient.configureCredentials(rootCA, private_key, certificate)
mqttClient.configureAutoReconnectBackoffTime(1, 32, 20)
mqttClient.configureConnectDisconnectTimeout(10)  # 10 sec
mqttClient.configureMQTTOperationTimeout(5)  # 5 sec

# custom callback function to update the state of the door lock upon receiving an update on the subscribed topic
def custom_callback(client, userdata, message):
        logger.info('Message recieved from {} topic'.format(message.topic)) # log that the message was received on the subscribed topic

        payload = message.payload # store the message payload
        payload_dict = json.loads(payload) # convert the payload to JSON format

        # select the desired state of door lock from the JSON payload to see whether the door needs to be locked or unlocked
        doorLock = payload_dict["current"]["state"]["desired"]["door_unlocked"] 

        # if the desired status is true (door unlocked) and the door is not already unlocked from Alexa, unlock the door and update the reported state
        if doorLock == "true" and GPIO.is_door_unlocked_from_alexa() == False:
            # reported state update message payload that the door is now unlocked
            reported_payload = {
                                    'state': {
                                        'reported': {
                                            'door_unlocked': 'true'
                                        }
                                    }
                              
                                }
            # unlock the door
            GPIO.unlock_door()
            # convert the reported payload to JSON format
            JSON_payload = json.dumps(reported_payload)
            # publish the reported state update to the update topic
            mqttClient.publish(update_topic, JSON_payload, 0)

        # if the desired status is false (door locked) and the door is already unlocked from Alexa, lock the door and update the reported state
        elif doorLock == "false" and GPIO.is_door_unlocked_from_alexa() == True:
            # reported state update message payload that the door is now unlocked
            reported_payload = {
                                    'state': {
                                        'reported': {
                                            'door_unlocked': 'false'
                                        }
                                    }
                                }
            # lock the door
            GPIO.lock_door()
            # convert the reported payload to JSON format
            JSON_payload = json.dumps(reported_payload)
            # publish the reported state update to the update topic
            mqttClient.publish(update_topic, JSON_payload, 0)
        
# main function of the program that initializes the MQTT connection and starts an infinite loop to keep MQTT connection alive and listen for knocks
def run_app(set_desired_state=False):
        # reported state startimg message payload that the door is locked (door is always locked on startup)
        start_payload = {
                            'state': {
                                'reported': {
                                    'door_unlocked': 'false'
                                }
                            }
                        }
        
        # start the MQTT client connection
        mqttClient.connect()

        # convert the reported payload to JSON format
        JSON_payload = json.dumps(start_payload)
        # set the publish topic where the updates will be published
        mqttClient.publish(update_topic, JSON_payload, 0)
        # subscribe to the update documents topic, upon receiving an update on this topic the custom callback is called
        mqttClient.subscribe(update_documents_topic, 1, custom_callback)

        # start an infinite loop to keep MQTT connection alive and listen for knocks
        while True:
            knock_detection.knock_detection()
            

# initualize the program
# when encountered a keyboard interrupt, cleanup the GPIO in order to exit cleanly
try:
    run_app()
except KeyboardInterrupt:
                logger.info("Closing upon keyboard interrupt.")
                GPIO.GPIO.cleanup()