FROM alephdata/followthemoney

RUN apt-get -qq -y update \
    && apt-get -qq -y install python3-pil \
    tesseract-ocr libtesseract-dev libleptonica-dev pkg-config tesseract-ocr-eng \
    libproj-dev libgeos++ \
    && apt-get -qq -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . /memorious
RUN pip3 install --no-cache-dir -e "/memorious[dev,ocr]"
WORKDIR /memorious

ENV MEMORIOUS_BASE_PATH=/data \
    MEMORIOUS_INCREMENTAL=true
