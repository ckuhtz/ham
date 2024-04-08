Python code to decode multicast sent from WSJT-X to 224.0.0.1 2237/udp and dumps parsed, decoded info with hexdump onto console. 

1. POC to extract information from QDatastream frame
2. Evolution of (1) to publish all WSJT-X outbound messages as JSON to Redis pubsub

N.B. This is a development/debugging tool, not a tool for a production purpose.
