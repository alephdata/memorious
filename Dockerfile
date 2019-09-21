FROM alpine:3.10

RUN apk add --no-cache python3 py3-icu py3-pillow py3-lxml py3-psycopg2 py3-gunicorn py3-cryptography p7zip tesseract-ocr
RUN apk add --no-cache --virtual=build_deps python3-dev g++ tesseract-ocr-dev musl-dev && \
    pip3 install --no-cache-dir tesserocr regex && \
    apk del build_deps
ENV OMP_THREAD_LIMIT=1

RUN pip3 install --no-cache-dir -U pip setuptools six

COPY setup.py /memorious/
COPY memorious /memorious/memorious
WORKDIR /memorious
RUN pip3 install --no-cache-dir -e .

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true
