
import json

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from redis import Redis

from pymongo import MongoClient

from twitter_credentials import *

PUBLISH_CHANNEL = 'twitter_watcher'

class TwitterListener(StreamListener):
    def __init__(self):
        super().__init__()

        self.redis = Redis()

    def on_data(self, data):
        obj = json.loads(data) 
        if obj.get('text'):
            self.redis.publish(PUBLISH_CHANNEL, data)    
        return True

    def on_error(self, status):
        print(status)

def main(): 
    connection = MongoClient()
    db = connection.ver1
    keywords = list(db.keywords.find(None, {'_id': 0, 'keyword': 1}))
    keywords = [key['keyword'] for key in keywords]

    #This handles Twitter authentication and the connection to Twitter Streaming API
    l = TwitterListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = Stream(auth, l)
    # stream.sample()
    stream.filter(track=keywords)

if __name__ == '__main__':
    main()

