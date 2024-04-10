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


callsign = "AK7VV"
pskreporter_url = "https://retrieve.pskreporter.info/query?senderCallsign=" + callsign
redis_host = "docker"
redis_port = "6379"

# create Redis client

try:
    redis_client = redis.Redis(host=redis_host, port=redis_port)
except Exception as e:
    print("Redis init problem:", str(e))

while True:

    # retrieve PSK reporter data for callsign as XML string

    response = requests.get(pskreporter_url)
    xml_string = response.text

    # Convert the XML string to a Python dictionary
    data_dict = xmltodict.parse(xml_string,attr_prefix='')

    pubsub_message = json.dumps(data_dict)

    # publish to Redis pubsub

    try:
        redis_client.publish(
            'periodic',
            json.dumps(pubsub_message)
        )
    except Exception as e:
        print("Redis publish():", str(e))
