#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd

from gensim.summarization import keywords

import pika, redis

## RabbitMQ and Redis connection
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
redisHost = os.getenv("REDIS_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

## Redis tables
db_posts = redis.Redis(host=redisHost, db=1)
db_keywords = redis.Redis(host=redisHost, db=3)

class Keywords:

    def __init__(self, submissions=None):
        self.submissions = submissions
        self.freq_dict = {}
    
    def extract_keywords(self, text):
        try:
            return keywords(text).split("\n")
        except:
            print("Call to keywords failed")

    def populate_dict(self, keywords_list):
        if keywords_list == None:
            print("No keywords.")
            return

        for key in keywords_list:
            self.freq_dict[key] = self.freq_dict.get(key, 0) + 1

    def compute_keywords(self):
        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            text = str(post['title'] + post['body'])
            keywords_list = self.extract_keywords(text)
            self.populate_dict(keywords_list)

        top_keywords = sorted(self.freq_dict.keys(), key=lambda k: self.freq_dict[k], reverse=True)
        
        print(top_keywords)
        
        if len(top_keywords) < 10:
            return top_keywords
        
        return top_keywords[:10]

    def worker(self):
        return self.compute_keywords()

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
    
    keywords_ob = Keywords(pd.DataFrame(submissions))
    top_keywords = keywords_ob.worker()
    
    db_keywords.sadd(body['sub_name'], jsonpickle.encode(top_keywords))

def main():
    connection, channel = get_rabbitMQ()
    channel.exchange_declare(exchange='redditHandle', exchange_type='direct')
    result = channel.queue_declare(queue='worker_keywords', durable=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange='redditHandle', 
        queue=queue_name,
        routing_key='worker_keywords'
    )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()