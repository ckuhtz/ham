# 1. publish a periodic event on pubsub (e.g. 1 minute)

import json
import redis
import time

redis_host = "docker"
redis_port = "6379"

# create Redis client

try:
    redis_client = redis.Redis(host=redis_host, port=redis_port)
except Exception as e:
    print("Redis init problem:", str(e))

pubsub_message = {
    "type": "minute"
}

while True:
    try:
        redis_client.publish(
            'periodic',
            json.dumps(pubsub_message,pretty=True)
        )
    except Exception as e:
        print("Redis publish():", str(e))

    time.sleep(60) # 1 minute of nothingness