# 1. publish a periodic event on pubsub (e.g. 1 minute)

import json
import redis
import time

# create Redis client

try:
    redis_client = redis.Redis(host="docker", port=6379)
except Exception as e:
    print("Redis init problem:", str(e))

pubsub_message = {
    "type": "minute"
}

while True:
    try:
        redis_client.publish(
            'periodic',
            json.dumps(pubsub_message)
        )
    except Exception as e:
        print("Redis publish():", str(e))

    time.sleep(60) # 1 minute of nothingness