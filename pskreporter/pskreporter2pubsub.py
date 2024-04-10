# retrieve information from pskreporter.info
# https://www.pskreporter.info/pskdev.html
# 1. retrieve xml
# 2. convert to dict
# 3. convert to json
# 4. publish on redis pubsub
#
# pip install xmtodict
# pip install requests

import json
import xmltodict
import requests
import redis
import time


pskreporter_callsign = "AK7VV"
#pskreporter_timewindow = 5 * 60
pskreporter_url = "https://retrieve.pskreporter.info/query?senderCallsign=" + pskreporter_callsign
redis_host = "docker"
redis_port = "6379"
debug = True

# wait for periodic message

def wait_for_periodic(r, message_value, count):
    channel_name = 'periodic'
    message_to_wait_for = json.dumps({ "type": message_value })

    pubsub = r.pubsub()
    pubsub.subscribe(channel_name)
    
    message_count = 0
    while message_count < count:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            if message['data'].decode('utf-8') == message_to_wait_for:
                message_count += 1
        if debug:
            print(f"Received '{message_to_wait_for}' for {message_count} out of {count} times.")
        if message_count < count:
            time.sleep(31) # wait 31 seconds before checking again

    if debug:
        print ("wait is over.")

# create Redis client

if debug:
    print("creating redis client")

try:
    redis_client = redis.Redis(host=redis_host, port=redis_port)
except Exception as e:
    print("Redis init problem:", str(e))

while True:

    # wait for 5 minutes so we don't trip the rate limiting for PSKreporter

    if debug:
        print("waiting for 5 minutes..")
    wait_for_periodic(redis_client, "minute", 5)

    # retrieve PSK reporter data for callsign as XML string

    if debug:
        print("getting PSKreporter data:", pskreporter_url)
    response = requests.get(pskreporter_url)
    xml_string = response.text

    # Convert the XML string to a Python dictionary
    data_dict = xmltodict.parse(xml_string,attr_prefix='')

    pubsub_message = json.dumps(data_dict)

    # publish to Redis pubsub

    try:
        redis_client.publish(
            'pskreporter',
            json.dumps(pubsub_message)
        )
        if debug:
            print("Redis pubsub <<", pubsub_message)
    except Exception as e:
        print("Redis publish():", str(e))
