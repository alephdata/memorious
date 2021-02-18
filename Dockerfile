FROM alpine:3.13.2

RUN apk add --no-cache python3 py3-pip py3-icu py3-pillow py3-lxml py3-psycopg2 p7zip tesseract-ocr
RUN pip3 install --no-cache-dir -U pip setuptools six wheel gunicorn
RUN apk add --no-cache --virtual=build_deps python3-dev g++ tesseract-ocr-dev musl-dev libffi-dev openssl-dev && \
    pip3 install --no-cache-dir tesserocr regex
ENV OMP_THREAD_LIMIT=1

COPY setup.py /memorious/
RUN pip3 install --no-cache-dir -e /memorious
COPY memorious /memorious/memorious

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true
