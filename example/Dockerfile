FROM alephdata/memorious:latest

COPY setup.py /crawlers/
COPY src /crawlers/src
RUN pip install -q -e /crawlers
COPY config /crawlers/config

ENV MEMORIOUS_CONFIG_PATH=/crawlers/config \
    MEMORIOUS_DATABASE_URI=postgresql://funes:funes@postgres/memorious \
    MEMORIOUS_BROKER_URI=amqp://guest:guest@rabbitmq:5672 \
    MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_EAGER=false \
    MEMORIOUS_DEBUG=false
