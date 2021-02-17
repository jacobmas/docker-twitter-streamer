FROM python:3.7.8-slim

# Build Args
ARG BUILD_DATE=None
ARG VCS_REF=None
ARG BUILD_VERSION=None

# Labels.
LABEL maintainer="jacob.alperin-sheriff@qs-2.com" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=${BUILD_DATE} \
      org.label-schema.name="QS2/social-streamer" \
      org.label-schema.description="QS-2 social streamer image" \
      org.label-schema.url="https://1904labs.com/" \
      org.label-schema.vcs-url="https://github.com/jacobmas/docker-twitter-streamer" \
      org.label-schema.vcs-ref=${VCS_REF} \
      org.label-schema.vendor="QS-2" \
      org.label-schema.version=${BUILD_VERSION} \
      org.label-schema.docker.cmd="docker run --rm 1904labs/twitter_stream:latest -f '#funny' -k \$TWITTER_CONSUMER_KEY -s \$TWITTER_CONSUMER_SECRET -a \$TWITTER_ACCESS_TOKEN -t \$TWITTER_ACCESS_TOKEN_SECRET"

RUN set -ex && \
  pip install kafka-python==2.0.1 tweepy==3.9.0 boto3==1.13.23 pyparsing==2.4.7 praw==7.1.4

COPY src /opt/bin
RUN set -ex && \
  chmod 755 /opt/bin/social_streamer.py

ENTRYPOINT [ "/opt/bin/social_streamer.py" ]
