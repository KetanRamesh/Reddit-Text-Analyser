#! usr/bin/env python3

from flask import Flask, request, Response, render_template
from flask_cors import CORS

app = Flask(__name__, static_url_path='', template_folder = ".", static_folder='.')
CORS(app)

## Flask app routes
@app.route('/', methods=['GET'])
def hello():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)