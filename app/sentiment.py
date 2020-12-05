#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd
import datetime as dt

import praw
from praw.models import MoreComments
from detoxify import Detoxify

import pika

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

## RabbitMQ connection
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

class Sentiment:

    def __init__(self, param=None, sub=None, limit=None):
        self.auth_param = param
        self.sub = sub
        self.limit = limit
        self.reddit = None
        self.submissions = {}

    ## Remove in final version
    def connectReddit(self):
        try:
            self.reddit = praw.Reddit(
                client_id=self.auth_param['client_id'],
                client_secret=self.auth_param['client_secret'],
                user_agent="sentiment"
            )
            print("Connection to Reddit successful.")
        except:
            print("Error connecting to Reddit.")

    ## Replace with Firebase retrieval code
    def getSubmissions(self):
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

    def computeSentiment(self):
        senti_count = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        sia = SentimentIntensityAnalyzer()
        sentiments = []

        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            text = post['title']
            score = sia.polarity_scores(text)
            score['headline'] = text
            sentiments.append(score)

        for sentiment in sentiments:
            if not sentiment['neg'] > 0.05:
                if sentiment['pos'] - sentiment['neg'] > 0:
                    senti_count['positive'] += 1
                else:
                    senti_count['neutral'] += 1
            elif not sentiment['pos'] > 0.05:
                if sentiment['pos'] - sentiment['neg'] <= 0:
                    senti_count['negative'] += 1
                else:
                    senti_count['neutral'] += 1
            else:
                senti_count['neutral'] += 1
        
        print(senti_count)

    def getToxicity(self):
        toxic_count = {
            "very_toxic": 0,
            "toxic": 0,
            "hard_to_say": 0,
            "not_toxic": 0
        }

        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            text = post['title']
            label = Detoxify('original').predict(text)
            print(label)

    def worker(self):
        self.connectReddit()
        self.getSubmissions()
        self.computeSentiment()
        # self.getToxicity()

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

def callback(ch, method, properties, body):
    body = jsonpickle.decode(body)

def main():
    _, channel = getRabbitMQ()
    channel.exchange_declare(exchange='sentimentWorker', exchange_type='direct')
    result = channel.queue_declare(queue='worker_sentiment', durable=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange='sentimentWorker', 
        queue=queue_name,
        routing_key='worker_sentiment'
    )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    # main()
    auth_file = '../auth.json'
    sub = 'learnpython'
    limit = 100
    
    with open(auth_file) as auth_param:
        param = json.load(auth_param)
    
    sentiment = Sentiment(param, sub, limit)
    sentiment.worker()