#! usr/bin/env python3

from flask import Flask, request, Response
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
import pandas as pd

from google.cloud import datastore

import praw

redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
projectId = os.getenv("GCLOUD_PROJECT") or "datacenter-292401"

app = Flask(__name__)

auth_file = '../auth.json'
with open(auth_file) as param:
    auth_param = json.load(param)

limit = 1

def get_rabbitMQ():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
    except:
        print("Can't connect RabbitMQ")
        return

    return connection, channel

def get_datastore():
    datastore_client = datastore.Client(projectId)
    return datastore_client

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

def store_submissions(submissions):
    datastore_client = get_datastore()
    # try:
    key = datastore_client.key('Posts')
    post_entity = datastore.Entity(key=key)
    for ind in range(len(submissions)):
        post = submissions.loc[ind]
        post_entity[post['id']] = post['title']
        datastore_client.put(post_entity)
    # except:
    #     print('Datastore problems')

## Flask app routes
@app.route('/', methods=['GET'])
def hello():
    return '<h1> Reddit Text Analyser </h1><p> Testing flask app </p>'

@app.route('/sentiment/<string:sub_name>', methods=['GET'])
def sentiment(sub_name):
    connection, channel = get_rabbitMQ()
    submissions = get_submissions(sub_name, limit)
    store_submissions(submissions)

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

@app.route('/keywords/<string:sub_name>', methods=['GET'])
def keywords(sub_name):
    connection, channel = get_rabbitMQ()
    submissions = get_submissions(sub_name, limit)
    store_submissions(submissions)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)