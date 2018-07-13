FROM alephdata/memorious:latest

COPY setup.py /crawlers/
COPY src /crawlers/src
RUN pip install -q -e /crawlers
COPY config /crawlers/config

ENV MEMORIOUS_CONFIG_PATH=/crawlers/config \
    MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_DEBUG=false \
    MEMORIOUS_REDIS_HOST=redis
