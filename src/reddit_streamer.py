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

def get_producer(args):
    if os.getenv("KAFKA_SERVICE_HOST", False):
        from kafka_producer import KafkaProducer
        return KafkaProducer()
    elif os.getenv("KAFKA_BOOTSTRAP_SERVER", False):
        from kafka_producer import KafkaProducer
        return KafkaProducer()
    elif os.getenv("KINESIS_STREAM_NAME", False):
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
    parser.add_argument('--subreddit',default='wallstreetbets')
    parser.add_argument('--redditor',default=None)#'AwayBed2714')

    parser.add_argument('--type', default='comments')
    parser.add_argument('--file',default=None, help='ConfigParser .ini file containing reddit credentials')
    parser.add_argument('--kinesis-api-name','--api',default='firehose')
    parser.add_argument('--kinesis-region','--region',default='us-west-2')
    parser.add_argument('--kinesis-stream-name', '--stream',default=None)

    args = parser.parse_args(incoming)
    args.producer = get_producer(args)
    print(f"args.producer={args.producer}")
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

