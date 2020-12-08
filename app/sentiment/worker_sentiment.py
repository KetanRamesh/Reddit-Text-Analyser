#! usr/bin/env python3

import os
import json
import jsonpickle
import pandas as pd

import pika, redis

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

## RabbitMQ and Redis connection
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
redisHost = os.getenv("REDIS_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

## Redis tables
db_posts = redis.Redis(host=redisHost, db=1)
db_sentiment = redis.Redis(host=redisHost, db=2)

class Sentiment:

    def __init__(self, submissions=None):
        self.submissions = submissions

    def compute_sentiment(self):
        senti_count = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        sia = SentimentIntensityAnalyzer()
        sentiments = []

        for i in range(len(self.submissions)):
            post = self.submissions.loc[i]
            text = str(post['body'] + post['title'])
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
        return senti_count

    def worker(self):
        return self.compute_sentiment()

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
    
    sentiment_ob = Sentiment(pd.DataFrame(submissions))
    senti_count = sentiment_ob.worker()
    
    db_sentiment.sadd(body['sub_name'], jsonpickle.encode(senti_count))

def main():
    connection, channel = get_rabbitMQ()
    channel.exchange_declare(exchange='redditHandle', exchange_type='direct')
    result = channel.queue_declare(queue='worker_sentiment', durable=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange='redditHandle', 
        queue=queue_name,
        routing_key='worker_sentiment'
    )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()  
