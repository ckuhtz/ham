# retrieve information from pskreporter.info
# https://www.pskreporter.info/pskdev.html
# 1. retrieve xml
# 2. convert to dict
# 3. convert to json
# 4. publish on redis pubsub

import json
import xmltodict

# Parse the XML file
with open('yourfile.xml', 'r') as file:
    xml_string = file.read()

# Convert the XML string to a Python dictionary
data_dict = xmltodict.parse(xml_string)

# Convert the Python dictionary to a JSON string
json_data = json.dumps(data_dict)

print(json_data)
