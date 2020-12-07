#! usr/bin/env python3

from flask import Flask, request, Response
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
import pandas as pd

import praw

redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
projectId = os.getenv("GCLOUD_PROJECT") or "datacenter-292401"

app = Flask(__name__)

auth_file = '../auth.json'
with open(auth_file) as param:
    auth_param = json.load(param)

## Databases
db_posts = redis.Redis(host=redisHost, db=1)
db_sentiment = redis.Redis(host=redisHost, db=2)
db_keywords = redis.Redis(host=redisHost, db=3)

limit = 3

def get_rabbitMQ():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
    except:
        print("Can't connect RabbitMQ")
        return

    return connection, channel

def connect_reddit():
    try:
        reddit = praw.Reddit(
            client_id=auth_param['client_id'],
            client_secret=auth_param['client_secret'],
            user_agent="reddit_scrapper"
        )
        print("Connection to Reddit successful.")
        return reddit
    except:
        print("Error connecting to Reddit.")
        return

def get_submissions(sub, limit):
    reddit = connect_reddit()
    submissions = {
        "id": [],
        "title": [],
        "body": [],
    }

    for submission in reddit.subreddit(sub).top(limit=limit):
        submissions['id'].append(submission.id)
        submissions['title'].append(submission.title)
        submissions['body'].append(submission.selftext)

    submissions = pd.DataFrame(submissions)
    return submissions

## Flask app routes
@app.route('/', methods=['GET'])
def hello():
    return '<h1> Reddit Text Analyser </h1><p> Testing flask app </p>'

@app.route('/sentiment/<string:sub_name>', methods=['GET'])
def sentiment(sub_name):
    connection, channel = get_rabbitMQ()
    if db_sentiment.exists(sub_name):
        message = {
            'sentiment': db_sentiment.smembers(sub_name)
        }
        message = jsonpickle.encode(message)
        return Response(response=message, status=200, mimetype='application/json')
    elif db_posts.exists(sub_name):
        message = {
            'sub_name': sub_name
        }

        message = jsonpickle.encode(message)
        channel.basic_publish(
            exchange='redditHandle',
            routing_key='worker_sentiment',
            body=message
        )
        connection.close()
        return Response(response=message, status=200, mimetype='application/json')
    else:
        print('Post submissions to reddit')

@app.route('/keywords/<string:sub_name>', methods=['GET'])
def keywords(sub_name):
    connection, channel = get_rabbitMQ()
    if db_keywords.exists(sub_name):
        message = {
            'keywords': db_keywords.smembers(sub_name)
        }
        message = jsonpickle.encode(message)
        return Response(response=message, status=200, mimetype='application/json')
    elif db_posts.exists(sub_name):
        message = {
            'sub_name': sub_name
        }

        message = jsonpickle.encode(message)
        channel.basic_publish(
            exchange='redditHandle',
            routing_key='worker_keywords',
            body=message
        )
        connection.close()
        return Response(response=message, status=200, mimetype='application/json')
    else:
        print('Post submissions to reddit')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)