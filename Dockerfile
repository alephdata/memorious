FROM alephdata/base:develop
MAINTAINER Friedrich Lindenberg <friedrich@pudo.org>
ENV DEBIAN_FRONTEND noninteractive

RUN pip install -q --upgrade pip && pip install -q --upgrade setuptools

COPY . /memorious
WORKDIR /memorious
RUN pip install -q -e .

CMD memorious.cli:main