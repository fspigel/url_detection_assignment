from flask import Flask
from flask.globals import request
from markupsafe import escape
from getaddressbar import get_address_bar
import requests
import numpy as np
from cv2 import imread
# from flask_cors import CORS
import time
app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin: *'


@app.route('/')
def index():
    return 'Hello!'


@app.route('/detect_url/')
def detect_url():
    img_url = request.args.get('img_url')
    print('request received: '+img_url)
    r = requests.get(url=img_url, stream=True)
    with open('incoming_img.png', 'wb') as f:
        for chunk in r:
            f.write(chunk)
    url = get_address_bar(imread('incoming_img.png'))
    return {'derived_url': url}
