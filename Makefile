DOCKER=docker run -v $(PWD)/dist:/memorious/dist -ti ghcr.io/alephdata/memorious
COMPOSE=docker-compose -f docker-compose.dev.yml

.PHONY: all clean build dev rebuild test services shell image

all: clean

clean:
	rm -rf dist build .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

build:
	docker build -t ghcr.io/alephdata/memorious .

dev:
	$(COMPOSE) build
	$(COMPOSE) run shell

rebuild:
	docker build --pull --no-cache -t ghcr.io/alephdata/memorious .

test:
	# Check if the command works
	memorious list
	pytest --cov=memorious --cov-report term-missing

services:
	$(COMPOSE) up -d httpbin proxy

shell:
	$(COMPOSE) run shell

image:
	docker build -t ghcr.io/alephdata/memorious .
