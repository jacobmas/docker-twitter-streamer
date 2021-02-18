# stdlib
import os
import sys
import logging

# addlib
import boto3

log = logging.getLogger(__name__)


class RecordAccumulator(object):

    def __init__(self, limit=20):
        self.limit = limit
        self.container = []

    def empty(self):
        result, self.container = self.container, []
        return result

    def full(self):
        return True if len(self.container) >= self.limit else False

    def append(self, record):
        self.container.append(record)


class KinesisProducer(object):
    def __init__(self, api_name, region_name, stream_name, partition_key='DEFAULT'):
        self.api_name = api_name
        self.client = boto3.client(api_name, region_name=region_name)
        self.stream_name = stream_name
        self.partition_key = partition_key
        self.accumulator = RecordAccumulator()

    def send(self, topic, data):
        temp_record={"Data": data.encode('utf-8')}
        if self.api_name=='kinesis':
            temp_record['PartitionKey']=self.partition_key
        self.accumulator.append(temp_record)
        if self.accumulator.full():
           if self.api_name=='firehose':
                return self.client.put_record_batch(
                    Records=self.accumulator.empty(),
                    DeliveryStreamName=self.stream_name)
           elif self.api_name=='kinesis':
                return self.client.put_records(
                    Records=self.accumulator.empty(),
                    StreamName=self.stream_name)
           else:
                raise Exception(f"Invalid api choice for KinesisProducer={self.api_name}")
        else:
            return True


class StdoutProducer(object):

    def send(self, topic, data):
        print(f"{topic}: {data}\n")
        return True