from gensim.summarization import keywords
import os
import json
import jsonpickle
import pandas as pd
import datetime as dt

import praw
from praw.models import MoreComments
import pika

rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

class extract_keywords:
    def __init__(self, reddit_handle = None):
        self.reddit_handle = reddit_handle
        self.freq_dict = {}
        self.posts = []
    #establish connection with redis an
    def connect_db(self):
    
    #retreive posts from redis and return list of posts and its content
    def retrieve_posts(self):
    
    def extract_keywords(self, post):
        try:
            return keywords(post).split("\n")
        except:
            print("call to keywords failed")

    def populate_dict(self, keywords_list):
        for key in keywords_list:
            d[key] = d.get(key, 0) + 1

    def compute_top_ten_keywords():
        top_keywords = sorted(self.freq_dict.keys(), key=lambda k: self.freq_dict[k], reverse=True)
        if len(top_keywords) < 10:
            return top_keywords
        return top_keywords[:10]


    def keywords_main():
        connect_db()
        retrieve_posts()
        for post in self.posts:
            self.populate_dict(self.extract_keywords(post))
        top_keywords = self.compute_top_ten_keywords()
        #populate the database with key - reddit handle and value as keywords

def getRabbitMQ():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
        print("Connection to RabbitMQ successful.")
    except:
        print("Error connecting to RabbitMQ.")
        return

    return connection, channel


def callback(self, ch, method, properties, body):
        body = jsonpickle.decode(body)
        extract_keywords e(body['sub_name'])
        e.keywords_main()

def start_consuming(self):
        _, channel = getRabbitMQ()
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
    start_consuming()