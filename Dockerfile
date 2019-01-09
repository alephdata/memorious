FROM alpine:edge

RUN apk update && apk upgrade && \
    apk add --no-cache python3 py3-icu py3-pillow py3-lxml py3-psycopg2 py3-gunicorn py3-cryptography musl-dev p7zip

RUN apk add tesseract-ocr

RUN pip3 install --upgrade pip setuptools

RUN apk add --no-cache --virtual=build_deps python3-dev g++ tesseract-ocr-dev && \
    pip3 install --no-cache-dir tesserocr alephclient regex && \
    apk del build_deps

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true

COPY setup.py /memorious/
COPY memorious /memorious/memorious
WORKDIR /memorious
RUN pip3 install -e .
