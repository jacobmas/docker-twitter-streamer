#!/usr/bin/env python3
"""Social streamer class
"""
# stdlib
import os
import sys
import logging
import argparse
import configparser
import time
from traceback import print_tb

# include path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# addlib
from praw_stream import PrawStream
from tweepy_stream import TweepyStream

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
log = logging.getLogger(__name__)

class SocialException(Exception):
    """Invalid SubRedditException."""

    def __init__(self, message):
        self.message = "Social exception "+message

class SocialStream:
    site_list = ['twitter', 'reddit']
    def __init__(self,args):
        self.result=self.get_args(args)
        if self.result['site']=='twitter':
            self.stream = TweepyStream(**self.result).filter(track=self.result['filter'])
        if self.result['site']=='reddit':
            # No built-in filter function for PrawStream
            self.stream = PrawStream(**self.result)#.filter(track=self.result['filter'])
    def get_producer(self,args):
        if os.getenv("KINESIS_STREAM_NAME", False):
            api_name = os.environ.get("KINESIS_API_NAME", 'firehose')
            region_name = os.environ.get("KINESIS_REGION", 'us-west-2')
            stream_name = os.environ.get("KINESIS_STREAM_NAME", 'TwitterStream')
            from kinesis_producer import KinesisProducer
            return KinesisProducer(api_name, region_name, stream_name)
        elif args.kinesis_stream_name is not None:
            # fails if not all are set
            api_name = args.kinesis_api_name
            region_name = args.kinesis_region
            stream_name = args.kinesis_stream_name
            from kinesis_producer import KinesisProducer
            return KinesisProducer(api_name, region_name, stream_name)
        else:
            from kinesis_producer import StdoutProducer
            return StdoutProducer()

    def parse_config_file(self, args):
        """ Parse a config file for credentials"""
        config = configparser.ConfigParser(interpolation=None)
        config.read(args.file)
        args.site=args.site.lower()
        for key in config[args.site]:
            print(f"key={key}, config[{args.site}][key]={config[args.site][key]}")
            setattr(args,key,config[args.site][key])

    def check_args(self,args):

        if not args.filter:
            twitter_api_filter = os.environ.get("TWITTER_API_FILTER")
            if twitter_api_filter:
                args.filter = [twitter_api_filter]
            else:
                args.filter = ['#']
        if args.site.lower() not in self.site_list:
            raise Exception(f"Invalid site selected, valid sites are {self.site_list}")
        if args.site.lower()=='twitter':
            if not args.consumer_key:
                raise Exception("Missing twitter api consumer key")
            if not args.consumer_secret:
                raise Exception("Missing twitter api consumer secret")
            if not args.access_token:
                raise Exception("Missing twitter api access token")
            if not args.access_token_secret:
                raise Exception("Missing twitter api access token secret")
        if args.site.lower()=='reddit':
            if not args.username:
                raise Exception("Missing reddit username")
            if not args.password:
                raise Exception("Missing reddit passwod")
            if not args.user_agent:
                raise Exception("Missing reddit user agent")
            if not args.client_id:
                raise Exception("Missing reddit client id")
            if not args.client_secret:
                raise Exception("Missing reddit client secret")

        return vars(args)



    def get_args(self,incoming = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--filter', action='append',help="Currently non-functional filter for stream")
        parser.add_argument('--site',default='twitter',help="site to stream")
        parser.add_argument('--subreddit',default='wallstreetbets',help='Subreddit to stream (reddit only)')
        parser.add_argument('--redditor',default=None,help='Redditor to stream (reddit only?)')#'AwayBed2714')

        parser.add_argument('--type', default='comments',help="type of stream (Reddit only), i.e. comments or submissions for reddit")
        parser.add_argument('--file',default=None, help='ConfigParser .ini file containing credentials for website (twitter, reddit, etc)')
        parser.add_argument('--kinesis-api-name','--api',default='firehose')
        parser.add_argument('--kinesis-region','--region',default='us-west-2')
        parser.add_argument('--kinesis-stream-name', '--stream',default=os.environ.get("KINESIS_STREAM_NAME"))
        parser.add_argument('-k', '--consumer-key', default=os.environ.get("TWITTER_CONSUMER_KEY"),
                            help="Twitter consumer key")
        parser.add_argument('-s', '--consumer-secret', default=os.environ.get("TWITTER_CONSUMER_SECRET"),
                            help="Twitter consumer secret")
        parser.add_argument('-a', '--access-token', default=os.environ.get("TWITTER_ACCESS_TOKEN"),
                            help="Twitter access token")
        parser.add_argument('-t', '--access-token-secret', default=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
                            help="Twitter access token secret")
        parser.add_argument('--username', default=os.environ.get("REDDIT_USERNAME"),
                            help="Reddit username")
        parser.add_argument('--password', default=os.environ.get("REDDIT_PASSWORD"),
                            help="Twitter access token secret")
        parser.add_argument('--user-agent', default=os.environ.get("REDDIT_USER_AGENT"),
                            help="Twitter access token secret")
        parser.add_argument('--client-id', default=os.environ.get("REDDIT_CLIENT_ID"),
                            help="Twitter access token secret")
        parser.add_argument('--client-secret', default=os.environ.get("REDDIT_CLIENT_SECRET"),
                            help="Twitter access token secret")

        args = parser.parse_args(incoming)
        args.producer = self.get_producer(args)

        if args.file is not None:
            self.parse_config_file(args)
        return self.check_args(args)

if __name__ == "__main__":
    while True:
        try:
            stream=SocialStream(sys.argv[1:])
        except Exception as e:
            log.error(f"Error with social stream, will attempt to recover gracefully {e},"+
                      f"{print_tb(sys.exc_info()[2])}")
            time.sleep(2)