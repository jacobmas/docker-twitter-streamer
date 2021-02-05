# stdlib
import os
import sys
import logging

import praw

log = logging.getLogger(__name__)

class RedditException(Exception):
    """Invalid SubRedditException."""

    def __init__(self, message):
        self.message = message



class PrawStream:

    def __init__(self, **kwargs):
        producer = kwargs.pop("producer", StdoutProducer())
        filteron = kwargs.pop("filter", "#")  # TODO: determine schema next week
        self.datatype=kwargs.pop("type","submissions") # or comments
        self.subreddit=kwargs.pop("subreddit")
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
        subreddit = self.reddit.subreddit(self.subreddit)
        the_stream = subreddit.stream.comments(skip_existing=True) if self.datatype=='comments' else subreddit.stream.submissions(skip_existing=True)
        for data in the_stream:
            self.listener.on_data(data)



class PrawStreamListener:

    def __init__(self, producer, topic, datatype,subreddit):
        self.producer = producer
        self.topic = topic
        self.datatype = datatype
        self.subreddit=subreddit


    def on_data(self, data):
        self.producer.send(self.topic, data)
        return True

    def on_error(self, status):
        print("Error: " + str(status))

class StdoutProducer(object):

    def send(self, topic, data):
        print(f"{topic}: {data}\n")
        return True