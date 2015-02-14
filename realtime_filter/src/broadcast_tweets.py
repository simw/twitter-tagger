import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import asyncio
import asyncio_redis
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

from pymongo import MongoClient

from strex.parse import Parser
from strex.query_engines.jsonpath import JsonEngine

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

import json

# List of keys to extract from the tweet
keys = {
    'text': 'text',
    'in_reply_to_status_id': 'in_reply_to_status_id',
    'twitter_id': 'id',
    'coordinates': 'coordinates',
    'lang': 'lang',
    'created_at': 'created_at',
    'user': 'user.screen_name',
    'user_followers': 'user.followers_count',
    'user_friends': 'user.friends_count'
}

LOG_FREQ = 10

class TwitterRepeater(WebSocketServerProtocol):
    def __init__(self):
        super().__init__()

    def onConnect(self, request):
        print('Client connecting: {}'.format(request.peer))

    def onOpen(self):
        self.factory.register(self)

    def onMessage(self, payload, is_binary):
        if is_binary:
            print('Binary message received: {} bytes'.format(len(payload)))

        else:
            print("Text message received: {}".format(payload.decode('utf8')))

        # self.sendMessage(payload, is_binary)
        
    def onClose(self, wasClean, code, reason):
        self.factory.unregister(self)
        print("WebSocket connection closed: {}".format(reason))

class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url, debug = False, debugCodePaths = False):
        super().__init__(url, debug=debug, debugCodePaths=debugCodePaths)
        self.clients = []
        self.parser = Parser(None, JsonEngine) 
        self.tweet_count = 0
        self.rejected_count = 0

        self.init_ml()

    def init_ml(self):
        connection = MongoClient()
        db = connection.ver1

        prefs = list(db.likes.find())
        texts = [pref['text'] for pref in prefs]
        likes = [pref['like'] for pref in prefs]

        ngram_max = 1
        binary = False
        analyzer = 'word'

        self.vect = CountVectorizer(ngram_range=(1,ngram_max), binary=False, lowercase=True, analyzer=analyzer)
        X = self.vect.fit_transform(texts)
        y = likes

        self.clf = LogisticRegression()
        self.clf.fit(X, y)

    def register(self, client):
        if not client in self.clients:
            print("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))

    @asyncio.coroutine
    def subscribe_to_redis(self):
        connection = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        subscriber = yield from connection.start_subscribe()
        yield from subscriber.subscribe([ 'twitter_watcher' ])

        while True:
            reply = yield from subscriber.next_published()
            self.onTweet(reply.value)

        connection.close()

    def onTweet(self, tweet_data):
        tweet = json.loads(tweet_data)
        tweet = self.parser.parse(keys, tweet)
        X_new = self.vect.transform([tweet['text']]) 
        y_new = self.clf.predict(X_new)
        print('{},'.format(y_new[0]), end='')
        if y_new[0] == 1:
            tweet['like'] = 1
            self.broadcast(json.dumps(tweet))
            self.tweet_count += 1
            if self.tweet_count % LOG_FREQ == 0:
                print('Passed on {} tweets'.format(self.tweet_count))
        else:
            # Really, we wouldn't broadcast disliked tweets
            # But here, we'll do it and highlight on the other end
            tweet['like'] = 0
            self.broadcast(json.dumps(tweet))
            self.rejected_count += 1
            if self.rejected_count % LOG_FREQ == 0:
                print('Rejected {} tweets'.format(self.rejected_count))

def main():
    loop = asyncio.get_event_loop()
    
    factory = BroadcastServerFactory("ws://localhost:9000", debug=False)
    factory.protocol = TwitterRepeater
    coro = loop.create_server(factory, '127.0.0.1', 9000)
    server = loop.run_until_complete(coro)

    loop.create_task(factory.subscribe_to_redis()) 

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()

if __name__ == '__main__':
    main()
    
