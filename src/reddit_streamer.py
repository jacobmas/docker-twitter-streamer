#!/usr/bin/env python3

# stdlib
import os
import sys
import logging
import argparse
import configparser

# include path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# addlib
from praw_stream import PrawStream

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
log = logging.getLogger(__name__)

def get_producer():
    if os.getenv("KAFKA_SERVICE_HOST", False):
        from kafka_producer import KafkaProducer
        return KafkaProducer()
    elif os.getenv("KAFKA_BOOTSTRAP_SERVER", False):
        from kafka_producer import KafkaProducer
        return KafkaProducer()
    elif os.getenv("KINESIS_STREAM_NAME", False):
        api_name = os.environ.get("KINESIS_API_NAME", 'firehose')
        region_name = os.environ.get("KINESIS_REGION", 'us-east-1')
        stream_name = os.environ.get("KINESIS_STREAM_NAME", 'TwitterStream')
        from kinesis_producer import KinesisProducer
        return KinesisProducer(api_name, region_name, stream_name)
    else:
        from praw_stream import StdoutProducer
        return StdoutProducer()

def check_args(args):
    if not args.filter:
        twitter_api_filter = os.environ.get("TWITTER_API_FILTER")
        if twitter_api_filter:
            args.filter = [twitter_api_filter]
        else:
            args.filter = ['#']
    if not args.consumer_key:
        raise Exception("Missing twitter api consumer key")
    if not args.consumer_secret:
        raise Exception("Missing twitter api consumer secret")
    if not args.access_token:
        raise Exception("Missing twitter api access token")
    if not args.access_token_secret:
        raise Exception("Missing twitter api access token secret")
    return vars(args)


def get_args(incoming = None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter', action='append')
    parser.add_argument('-k', '--consumer_key', default=os.environ.get("TWITTER_CONSUMER_KEY"))
    parser.add_argument('-s', '--consumer_secret', default=os.environ.get("TWITTER_CONSUMER_SECRET"))
    parser.add_argument('-a', '--access_token', default=os.environ.get("TWITTER_ACCESS_TOKEN"))
    parser.add_argument('-t', '--access_token_secret', default=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"))
    parser.add_argument('--subreddit',default='judaism')
    parser.add_argument('--file',default=None)
    args = parser.parse_args(incoming)
    args.producer = get_producer()
    result=vars(args)
    print(result)
    if args.file is not None:
        config = configparser.ConfigParser()
        config.read(args.file)

        temp_dict={key:config['Reddit'][key] for key in config['Reddit']}
        print(temp_dict)
        for key in temp_dict:
            result[key]=temp_dict[key]

    print(result)
    return result

if __name__ == "__main__":
    args = get_args(sys.argv[1:])
    stream = PrawStream(**args).filter(track=args['filter'])

