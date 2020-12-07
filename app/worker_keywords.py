#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd
import datetime as dt

import praw

from gensim.summarization import keywords

import pika
import redis

## RabbitMQ connection
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
redisHost = os.getenv("REDIS_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

db_posts = redis.Redis(host=redisHost, db=1)
db_sentiment = redis.Redis(host=redisHost, db=2)

class Keywords:

    def __init__(self, param=None, sub=None, limit=None):
        self.auth_param = param
        self.sub = sub
        self.limit = limit
        self.reddit = None
        self.freq_dict = {}
        self.submissions = {}

    ## Remove in final version
    def connect_reddit(self):
        try:
            self.reddit = praw.Reddit(
                client_id=self.auth_param['client_id'],
                client_secret=self.auth_param['client_secret'],
                user_agent="keywords"
            )
            print("Connection to Reddit successful.")
        except:
            print("Error connecting to Reddit.")

    ## Replace with database retrieval
    def get_submissions(self):
        self.submissions = {
            "id": [],
            "title": [],
            "body": [],
            "comm_num": [],
            "url": []
        }

        for submission in self.reddit.subreddit(self.sub).top(limit=self.limit):
            self.submissions['id'].append(submission.id)
            self.submissions['title'].append(submission.title)
            self.submissions['body'].append(submission.selftext)
            self.submissions['comm_num'].append(submission.num_comments)
            self.submissions['url'].append(submission.url)

        self.submissions = pd.DataFrame(self.submissions)
    
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
        
        print('Keywords: ')
        print(top_keywords)
        # return top_keywords[:10]

    def worker(self):
        self.compute_keywords()

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
    print(submissions)
    keywords_ob = Keywords()
    keywords_ob.submissions = pd.DataFrame(submissions)
    keywords_ob.worker()

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
    # auth_file = '../auth.json'
    # sub = 'learnpython'
    # limit = 100
    
    # with open(auth_file) as auth_param:
    #     param = json.load(auth_param)
    
    # keywords_ob = Keywords(param, sub, limit)
    # keywords_ob.worker()
