DOCKER=docker run -v $(PWD)/dist:/memorious/dist -ti alephdata/memorious

all: clean

clean:
	rm -rf dist build .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

build:
	docker build -t alephdata/memorious .

rebuild:
	docker build --pull --no-cache -t alephdata/memorious .

test:
	pytest --cov=memorious --cov-report term-missing

ui:
	python memorious/ui/views.py

shell:
	$(DOCKER) sh

image:
	docker build -t alephdata/memorious .
