FROM python:3.7
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq -y update && apt-get -qq -y dist-upgrade \
    && apt-get -qq -y install python-pip build-essential python-dev \
        libxml2-dev libxslt1-dev libpq-dev apt-utils ca-certificates \
        libjpeg62-turbo libtiff5-dev libjpeg-dev zlib1g-dev libleptonica-dev \
        libtesseract-dev libicu-dev tesseract-ocr-eng p7zip-full \
    && apt-get -qq -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true

RUN pip install -q --upgrade pip && pip install -q --upgrade setuptools \
    && pip install -q --upgrade pyicu lxml pillow requests[security] gunicorn

COPY setup.py /memorious/
COPY memorious /memorious/memorious
WORKDIR /memorious
RUN pip install -q -e .
