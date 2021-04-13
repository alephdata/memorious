DOCKER=docker run -v $(PWD)/dist:/memorious/dist -ti alephdata/memorious
COMPOSE=docker-compose -f docker-compose.dev.yml

all: clean

clean:
	rm -rf dist build .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

build:
	docker build -t alephdata/memorious .

dev:
	$(COMPOSE) build
	$(COMPOSE) run shell

rebuild:
	docker build --pull --no-cache -t alephdata/memorious .

test:
	# Check if the command works
	memorious list
	pytest --cov=memorious --cov-report term-missing

shell:
	$(COMPOSE) run shell

image:
	docker build -t alephdata/memorious .
