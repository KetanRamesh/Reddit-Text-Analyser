#! usr/bin/env python3

from flask import Flask, request, Response
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json

redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

app = Flask(__name__)

def getRabbitMQ():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
    except:
        print("Can't connect RabbitMQ")
        return

    return connection, channel

# def getFirestore():
#     cred = credentials.ApplicationDefault()
#     firebase_admin.initialize_app(cred, {
#         'projectId': 'test',
#     })
#     db = firestore.client()
#     return db


@app.route('/', methods=['GET'])
def hello():
    return '<h1> Reddit Text Analyser </h1><p> Testing flask app </p>'


@app.route('/sentiment/<string:sub_name>', methods=['GET'])
def sentiment(sub_name):
    connection, channel = getRabbitMQ()

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
    connection, channel = getRabbitMQ()

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
