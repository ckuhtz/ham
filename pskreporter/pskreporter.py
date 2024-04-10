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
pskreporter_timewindow = 5 * 60
pskreporter_url = "https://retrieve.pskreporter.info/query?senderCallsign=" + pskreporter_callsign + "?flowStartSeconds=-" + str(pskreporter_timewindow)
debug = True

# retrieve PSK reporter data for callsign as XML string

if debug:
    print("getting PSKreporter data.")
response = requests.get(pskreporter_url)
xml_string = response.text

# Convert the XML string to a Python dictionary
data_dict = xmltodict.parse(xml_string,attr_prefix='')

pubsub_message = json.dumps(data_dict)

# publish to Redis pubsub

if debug:
    print(pubsub_message)
