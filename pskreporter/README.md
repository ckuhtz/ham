pskreporter2pubsub.py checks for periodic messages from redis 
pubsub. once no less than 5 minutes have passed, PSK reporter 
is queried for info for specific callsign.