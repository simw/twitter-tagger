
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId

import json

DEBUG = True

app = Flask(__name__,
    static_folder='../webclient', 
    static_url_path='/static',
    template_folder='../templates')

def connect():
    client = MongoClient()
    db = client.ver1
    return db

db = connect()

@app.route('/tagging', methods=['GET'])
def tagging():
    sortby = '_id'
    if request.args.get('sort'):
        sortby = request.args.get('sort')
    tweets = list(db.taggedtweets.find().sort(sortby, -1).limit(300))
    return render_template('tagging.html', tweets=tweets)

@app.route('/tagged', methods=['GET'])
def tagged():
    likes = list(db.likes.find({'like': 1}).sort('_id', -1).limit(100))
    dislikes = list(db.likes.find({'like': 0}).sort('_id', -1).limit(100))
    return render_template('tagged.html', likes=likes, dislikes=dislikes)

@app.route('/tag/like', methods=['POST'])
def like_tweet():
    data = request.get_json()
    tweet_id = data['id']
    tweet = db.taggedtweets.find_one({'_id': ObjectId(tweet_id)})
    tweet['like'] = 1
    db.likes.insert(tweet)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/tag/dislike', methods=['POST'])
def dislike_tweet():
    data = request.get_json()
    tweet_id = data['id']
    tweet = db.taggedtweets.find_one({'_id': ObjectId(tweet_id)})
    tweet['like'] = 0
    db.likes.insert(tweet)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/tag/clear', methods=['POST'])
def clear_pref():
    data = request.get_json()
    tweet_id = data['id']
    tweet = db.likes.remove({'_id': ObjectId(tweet_id)})
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/', methods=['GET'])
@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html')

def main():
    if DEBUG:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
