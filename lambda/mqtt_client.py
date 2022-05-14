import boto3
import os
import json

host = os.environ.get('AWS_IOT_ENDPOINT')
port = os.environ.get('AWS_IOT_PORT')
thingName = os.environ.get('AWS_IOT_THINGNAME')
mqttClient = boto3.client('iot-data', 'eu-west-1')

def unlock_door():
    
    payload_dict = {
        'state': {
            'desired' : {
                'door_unlocked' : 'true'
            }
        }
    }
    
    publish_update(payload_dict)
    
def lock_door():
    
    payload_dict = {
        'state': {
            'desired' : {
                'door_unlocked' : 'false'
            }
        }
    }
    
    publish_update(payload_dict)
    
def publish_update(payload_dict):
    JSON_payload = json.dumps(payload_dict)
    response = mqttClient.update_thing_shadow(thingName=thingName, payload=JSON_payload)
    print(json.loads(response['payload'].read()))