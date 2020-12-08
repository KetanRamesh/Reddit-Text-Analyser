#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd

import pika, redis

from detoxify import Detoxify

## RabbitMQ and Redis connection
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
redisHost = os.getenv("REDIS_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

## Reddis tables
db_posts = redis.Redis(host=redisHost, db=1)
db_toxicity = redis.Redis(host=redisHost, db=4)

class Toxicity:

    def __init__(self, submissions=None):
        self.submissions = submissions

    def get_toxicity(self):
        toxic_count = {}

        for i in range(30):
            post = self.submissions.loc[i]
            text = str(post['title'] + post['body'])
            label = Detoxify('original').predict(text)
            toxic_count = {k: label.get(k, 0) + toxic_count.get(k, 0) for k in set(label) | set(toxic_count)}

        return toxic_count

    def worker(self):
        return self.get_toxicity()

def get_rabbitMQ():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
        print("Connection to RabbitMQ successful.")
    except:
        print("Error connecting to RabbitMQ.")
        return

    return connection, channel

def callback(ch, method, properties, body):
    body = jsonpickle.decode(body)
    submissions = list(db_posts.smembers(body['sub_name']))[0]
    submissions = jsonpickle.decode(submissions)
    
    toxicity_ob = Toxicity(pd.DataFrame(submissions))
    toxicity_index = toxicity_ob.worker()
    
    db_toxicity.sadd(body['sub_name'], jsonpickle.encode(toxicity_index))

def main():
    connection, channel = get_rabbitMQ()
    channel.exchange_declare(exchange='redditHandle', exchange_type='direct')
    result = channel.queue_declare(queue='worker_toxicity', durable=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange='redditHandle', 
        queue=queue_name,
        routing_key='worker_toxicity'
    )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()