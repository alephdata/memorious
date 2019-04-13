FROM alpine:3.9

RUN apk add --no-cache python3 py3-icu py3-pillow py3-lxml py3-psycopg2 py3-gunicorn py3-cryptography musl-dev p7zip
RUN apk add --no-cache --virtual=build_deps python3-dev g++ && \
    pip3 install --no-cache-dir grpcio regex

RUN pip3 install --no-cache-dir -U pip setuptools six

COPY setup.py /memorious/
COPY memorious /memorious/memorious
WORKDIR /memorious
RUN pip3 install --no-cache-dir -e .

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true
