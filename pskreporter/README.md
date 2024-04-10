pskreporter2pubsub.py checks for periodic messages from redis 
pubsub. once no less than 5 minutes have passed, PSK reporter 
is queried for info for specific callsign.

pskreporter.py is a stripped down version which queries PSK 
reporter one time and exits.