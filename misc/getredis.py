import redis
import time

redis_channel = 'pskreporter'

redis_host = "docker"
redis_port = "6379"

redis_client = redis.Redis(host=redis_host,port=redis_port)

pubsub = redis_client.pubsub()
pubsub.subscribe(redis_channel)

while True:
    message = pubsub.get_message()
    if message:
        print(message)
    time.sleep(0.001)