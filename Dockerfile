FROM python:3.7
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq -y update && apt-get -qq -y dist-upgrade \
    && apt-get -qq -y install python-pip build-essential python-dev \
        libxml2-dev libxslt1-dev libpq-dev apt-utils ca-certificates \
        libjpeg62-turbo libtiff5-dev libjpeg-dev zlib1g-dev \
        libtesseract-dev libicu-dev tesseract-ocr-eng p7zip-full \
    && apt-get -qq -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV TESSDATA_PREFIX /usr/share/tesseract-ocr \
    MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true \
    MEMORIOUS_EAGER=false \
    C_FORCE_ROOT=true

RUN pip install -q --upgrade pip && pip install -q --upgrade setuptools \
    && pip install -q --upgrade pyicu lxml requests[security] gunicorn

COPY setup.py /memorious/
COPY memorious /memorious/memorious
COPY ui /memorious/ui
WORKDIR /memorious
RUN pip install -q -e . && pip install -q -e ./ui


# Web ui:
# RUN gunicorn -t 300 memorious_ui:app

# Worker:
# RUN celery -A memorious.tasks -c 10 -l INFO worker