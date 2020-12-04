#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd
import datetime as dt

import praw
from praw.models import MoreComments
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

    def expandComments(self, morecomments):
        comments = morecomments.comments()
        if isinstance(comments, MoreComments):
            return self.expandComments(comments)
        
        return comments

    def getCommentsTree(self, morecomments):
        comments = []
        count = 5
        for comment in morecomments:
            if (count == 0):
                break
            post = self.reddit.comment(comment.id)
            comments.append(post.body)
            count -= 1
        
        return comments

    def getComments(self):
        self.comments = {}

        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            submission = self.reddit.submission(id=post['id'])
            submission.comment_limit = 3
            top_comments = submission.comments
            for comment in top_comments:
                if isinstance(comment, MoreComments):
                    comments = self.expandComments(comment)
                    comments = self.getCommentsTree(comments)
                    self.comments[post['id']] = comments
                    continue
                if post['id'] in self.comments:
                    self.comments[post['id']].append(comment.body)
                else:
                    self.comments[post['id']] = []
                    self.comments[post['id']].append(comment.body)

    def addComments(self):

        for ind in range(len(self.submissions['id'])):
            post_id = self.submissions['id'][ind]
            comments = self.comments[post_id]
            self.submissions['comments'] = comments

    def computeSentiment(self):
        sia = SentimentIntensityAnalyzer()
        sentiments = []

        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            text = post['title']
            score = sia.polarity_scores(text)
            score['headline'] = text
            sentiments.append(score)

    def worker(self):
        self.connectReddit()
        self.getSubmissions()
        self.getComments()
        self.computeSentiment()

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
    limit = 3
    
    with open(auth_file) as auth_param:
        param = json.load(auth_param)
    
    sentiment = Sentiment(param, sub, limit)
    sentiment.worker()