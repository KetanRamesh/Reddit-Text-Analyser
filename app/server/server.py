#! usr/bin/env python3

from flask import Flask, request, Response, render_template
from flask_cors import CORS
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import requests
import json
import pandas as pd

import praw

## RabbitMQ and Redis connection
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

app = Flask(__name__, static_url_path='', template_folder = ".", static_folder='.')
# CORS(app)

auth_file = './auth.json'
with open(auth_file) as param:
    auth_param = json.load(param)

## Databases
db_posts = redis.Redis(host=redisHost, db=1)
db_sentiment = redis.Redis(host=redisHost, db=2)
db_keywords = redis.Redis(host=redisHost, db=3)
db_toxicity = redis.Redis(host=redisHost, db=4)

limit = 1000

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

    #submissions = pd.DataFrame(submissions)
    return submissions

## Flask app routes
@app.route('/', methods=['GET'])
def hello():
    return '<h> Reddit Analyser </h>'
    # return render_template("index.html")

@app.route('/sentiment/<string:sub_name>', methods=['GET'])
def sentiment(sub_name):
    print("entered sentiment")
    connection, channel = get_rabbitMQ()
    if db_sentiment.exists(sub_name):
        print("sentiment exists")
        senti_count = list(db_sentiment.smembers(sub_name))[0]
        senti_count = jsonpickle.decode(senti_count)
        message = {
            'senti_count': senti_count
        }
        return json.dumps(message)
    elif db_posts.exists(sub_name):
        print("handle exists")
        message = {
            'sub_name': sub_name
        }

        channel.basic_publish(
            exchange='redditHandle',
            routing_key='worker_sentiment',
            body=jsonpickle.encode(message)
        )
        connection.close()
        return json.dumps(message)
    else:
        submissions = get_submissions(sub_name, limit)
        submissions = jsonpickle.encode(submissions)
        db_posts.sadd(sub_name, submissions)
        db_posts.wait(1, 5)
        if db_posts.exists(sub_name):
            print("none exist")
            message = {
                'sub_name': sub_name
            }

            channel.basic_publish(
                exchange='redditHandle',
                routing_key='worker_sentiment',
                body=jsonpickle.encode(message)
            )
            connection.close()
            return json.dumps(message)
        else:
            message = {
                'response': 'Failed'
            }

            return json.dumps(message)

@app.route('/keywords/<string:sub_name>', methods=['GET'])
def keywords(sub_name):
    connection, channel = get_rabbitMQ()
    if db_keywords.exists(sub_name):
        top_keywords = list(db_keywords.smembers(sub_name))[0]
        top_keywords = jsonpickle.decode(top_keywords)
        message = {
            'keywords': top_keywords
        }
        return json.dumps(message)
    elif db_posts.exists(sub_name):
        message = {
            'sub_name': sub_name
        }

        channel.basic_publish(
            exchange='redditHandle',
            routing_key='worker_keywords',
            body=jsonpickle.encode(message)
        )
        connection.close()
        return json.dumps(message)
    else:
        submissions = get_submissions(sub_name, limit)
        submissions = jsonpickle.encode(submissions)
        db_posts.sadd(sub_name, submissions)
        db_posts.wait(1, 5)
        if db_posts.exists(sub_name):
            message = {
                'sub_name': sub_name
            }

            channel.basic_publish(
                exchange='redditHandle',
                routing_key='worker_keywords',
                body=jsonpickle.encode(message)
            )
            connection.close()
            return json.dumps(message)
        else:
            message = {
                'response': 'Failed'
            }

            return json.dumps(message)

@app.route('/toxicity/<string:sub_name>', methods=['GET'])
def toxicity(sub_name):
    connection, channel = get_rabbitMQ()
    if db_toxicity.exists(sub_name):
        toxicity_index = list(db_toxicity.smembers(sub_name))[0]
        toxicity_index = jsonpickle.decode(toxicity_index)
        message = {
            'toxicity_index': toxicity_index
        }
        return json.dumps(message)
    elif db_posts.exists(sub_name):
        message = {
            'sub_name': sub_name
        }

        channel.basic_publish(
            exchange='redditHandle',
            routing_key='worker_toxicity',
            body=jsonpickle.encode(message)
        )
        connection.close()
        return json.dumps(message)
    else:
        submissions = get_submissions(sub_name, limit)
        submissions = jsonpickle.encode(submissions)
        db_posts.sadd(sub_name, submissions)
        db_posts.wait(1, 5)
        if db_posts.exists(sub_name):
            message = {
                'sub_name': sub_name
            }

            channel.basic_publish(
                exchange='redditHandle',
                routing_key='worker_toxicity',
                body=jsonpickle.encode(message)
            )
            connection.close()
            return json.dumps(message)
        else:
            message = {
                'response': 'Failed'
            }

            return json.dumps(message)

## Frontend-Server get methods
@app.route('/get_keywords/<string:sub_name>', methods=['GET'])
def get_keywords(sub_name):
    db_keywords.wait(1, 5)
    if db_keywords.exists(sub_name):
        top_keywords = list(db_keywords.smembers(sub_name))[0]
        top_keywords = jsonpickle.decode(top_keywords)
        message = {
            'keywords': top_keywords
        }
        return json.dumps(message)

    message = {
        'response': 'Try Again'
    }
    return json.dumps(message)

@app.route('/get_sentiment/<string:sub_name>', methods=['GET'])
def get_sentiment(sub_name):
    db_sentiment.wait(1, 5)
    if db_sentiment.exists(sub_name):
        senti_count = list(db_sentiment.smembers(sub_name))[0]
        senti_count = jsonpickle.decode(senti_count)
        message = {
            'senti_count': senti_count
        }
        return json.dumps(message)
    
    message = {
        'response': 'Try Again'
    }
    return json.dumps(message)

@app.route('/get_toxicity/<string:sub_name>', methods=['GET'])
def get_toxicity(sub_name):
    db_toxicity.wait(1, 5)
    if db_toxicity.exists(sub_name):
        toxicity_index = list(db_toxicity.smembers(sub_name))[0]
        toxicity_index = jsonpickle.decode(toxicity_index)
        message = {
            'toxicity_index': toxicity_index
        }
        message = json.dumps(message)
        return json.dumps(message)
    
    message = {
        'response': 'Try Again'
    }
    return json.dumps(message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)