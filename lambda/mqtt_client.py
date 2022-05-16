import boto3
import os
import json

# load the environmental variables
host = os.environ.get('AWS_IOT_ENDPOINT')
port = os.environ.get('AWS_IOT_PORT')
thingName = os.environ.get('AWS_IOT_THINGNAME')

# initialize the Boto3 MQTT client for IoT data transmission, with the IoT Thing region specified
mqttClient = boto3.client('iot-data', 'eu-west-1')

# function to load the payload to unlock the door
def unlock_door():
    
    payload_dict = {
        'state': {
            'desired' : {
                'door_unlocked' : 'true'
            }
        }
    }
    
    publish_update(payload_dict)
    
# function to load the payload to lock the door
def lock_door():
    
    payload_dict = {
        'state': {
            'desired' : {
                'door_unlocked' : 'false'
            }
        }
    }
    
    publish_update(payload_dict)

# function to publish the payload to the IoT Thing shadow topic
def publish_update(payload_dict):
    JSON_payload = json.dumps(payload_dict)
    mqttClient.update_thing_shadow(thingName=thingName, payload=JSON_payload)
