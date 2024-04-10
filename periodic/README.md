creates an event on the Redis pubsub channel 'periodic' with a JSON message 
specifying the type of periodic message.  Currently this is "minute", published 
no sooner than after one minute.