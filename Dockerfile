FROM alephdata/base:develop
ENV DEBIAN_FRONTEND noninteractive

RUN pip install -q --upgrade pip && pip install -q --upgrade setuptools

COPY setup.py /memorious/
COPY memorious /memorious/memorious
WORKDIR /memorious
RUN pip install -q -e .

COPY crawlers /crawlers
RUN pip install -q -e /crawlers

CMD memorious.cli:main