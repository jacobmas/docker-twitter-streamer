# stdlib
import os
import sys
import logging
import json
from json import JSONEncoder
import praw
from kinesis_producer import StdoutProducer

from twitter_query_parser import TwitterSeachQuery

log = logging.getLogger(__name__)

class RedditException(Exception):
    """Invalid SubRedditException."""

    def __init__(self, message):
        self.message = message

class PRAWJSONEncoder(JSONEncoder):
    """Class to encode PRAW objects to JSON."""
    def default(self, obj):
        if isinstance(obj, praw.models.base.PRAWBase):
            obj_dict = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    obj_dict[key] = value
            return obj_dict
        else:
            return JSONEncoder.default(self, obj)


class PrawStream:

    def __init__(self, **kwargs):
        producer = kwargs.pop("producer", StdoutProducer())
        filteron = kwargs.pop("filter", "")  # TODO: determine schema next week
        self.datatype=kwargs.pop("type","submissions") # or comments
        self.subreddit=kwargs.pop("subreddit",None)
        self.redditor=kwargs.pop("redditor",None)

        if self.datatype!='comments' and self.datatype!='submissions':
            raise RedditException("Only valid streams are comments, submissions")
        if self.subreddit=='all':
            raise RedditException("Cannot stream r/all due to space constraints")
        authkeys = ['username', 'password', 'client_id', 'client_secret','user_agent']
        authargs = {key: kwargs.pop(key) for key in authkeys}


        self.listener = PrawStreamListener(producer, filteron,self.datatype,self.subreddit)
        self.reddit = praw.Reddit(**authargs)

        self._stream()

    def _stream(self):
        ''' Actually stream the data, perhaps this should be called by init'''
        #super().__init__(**kwargs)
        # stream username, filter on subreddit if both are set
        reddit_stream=None
        if self.redditor is not None:
            log.error(f"self.redditor={self.redditor}")
            reddit_stream=self.reddit.redditor(self.redditor)
        elif self.subreddit is not None:
            reddit_stream=self.reddit.subreddit(self.subreddit)
        else:
            raise RedditException("Must specify subreddit or username")
        print(f"reddit_stream={reddit_stream}")
        the_stream = reddit_stream.stream.comments(skip_existing=True) if self.datatype=='comments' else subreddit.stream.submissions(skip_existing=True)
        for data in the_stream:
            self.listener.on_data(data)



class PrawStreamListener:

    def __init__(self, producer, topic, datatype,subreddit):
        self.producer = producer
        self.topic = " AND ".join(topic)
        #print(f"topic={self.topic}")
        self.query_obj = TwitterSeachQuery(self.topic) if topic else None
        self.datatype = datatype
        self.subreddit=subreddit


    def on_data(self, data):
        if self.query_obj is None or self.query_obj.evaluate_search(data.body):
            result=self.producer.send(self.topic, json.dumps(data, cls=PRAWJSONEncoder))
            print(f"result of send ={result}")
        return True

    def on_error(self, status):
        print("Error: " + str(status))

