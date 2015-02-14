from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import os
import sys

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from strex.parse import Parser
from strex.query_engines.jsonpath import JsonEngine

import json
from pymongo import MongoClient

from twitter_credentials import *

import logging

"""
Connects to twitter using dets in .twitter_credentials
Uses stream.filter to return tweets containing desired keywords
Then writes out tweets according to tags
"""

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

# Frequency of tweets to log on
freq = 10

class TaggingListener(StreamListener):
    def __init__(self, db, tagging_map, extra_tagging_map=None):
        super(TaggingListener, self).__init__()
        self.set_keywords(tagging_map, extra_tagging_map)
        self.db = db
        self.count = 0
        self.parser = Parser(None, JsonEngine)

        # self.logger = logging.getLogger('twitter_tagger')

    def set_keywords(self, tagging_map, extra_tagging_map=None):
        # Main keywords, on which the incoming tweets are filtered
        self.keywords = set(tagging_map.keys())
        self.tagging_map = tagging_map

        # Extra set for tagging, but not filtering
        # (ie a tweet with just one of these keywords will be missed,
        #  but one with a regular keyword will get an extra tag)
        self.extra_keywords = set(extra_tagging_map.keys())
        self.extra_tagging_map = extra_tagging_map

    def on_data(self, data):
        obj = json.loads(data) 
        if obj.get('text'):
            words = set(obj['text'].lower().split())
            found_keywords = words.intersection(self.keywords)

            if found_keywords:
                # Only save certain keys from the twitter data
                tweet = self.parser.parse(keys, obj)
                # tweet = {key: obj[key] for key in keys}

                # Construct a list of tags for the tweet
                tags = []
                for keyword in found_keywords:
                    tags += self.tagging_map[keyword].split()

                if self.extra_keywords:
                    found_extra_tags = words.intersection(self.extra_keywords)
                    for keyword in found_extra_tags:
                        tags += extra_tagging_map[keyword].split()

                tags = set(tags)
                tweet['keywords'] = list(tags)
                self.db.taggedtweets.insert(tweet)
                self.count += 1
                if self.count % freq == 0:
                    logging.info('Completed {} more tweets'.format(freq))

            self.db.alltweets.insert(obj)

        return True

    def on_error(self, status):
        print(status)

def get_keywords(db):
    # Keywords list stored in mongo as (key, tag(s)) table
    raw_keywords = list(db.keywords.find())
    if not raw_keywords:
        print('No keywords found in database')
        exit()

    tagging_map = {key['keyword']: key['tag'] for key in raw_keywords}

    raw_keywords = list(db.extrakeywords.find())
    extra_tagging_map = {key['keyword']: key['tag'] for key in raw_keywords}

    return (tagging_map, extra_tagging_map)

def main():        
    logging.basicConfig(
        filename='twitter_tagger.log',
        level=logging.INFO,
        format='%(asctime)s %(message)s', 
        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('Starting twitter tagger')

    client = MongoClient()
    db = client.ver1
    (tagging_map, extra_tagging_map) = get_keywords(db)
    logging.info('Using {} keywords'.format(len(tagging_map)))

    #This handles Twitter authetification and the connection to Twitter Streaming API
    l = TaggingListener(db, tagging_map, extra_tagging_map)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = Stream(auth, l)
    stream.filter(track=tagging_map.keys())
    # stream.sample()

if __name__ == '__main__':
    main()
