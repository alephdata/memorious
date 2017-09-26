
all: clean test dists

install: clean
	pip install -e .

test: install
	# nosetests

dists: install
	python setup.py sdist
	python setup.py bdist_wheel

release: dists
	pip install -q twine
	twine upload dist/*

clean:
	rm -rf dist build .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

build:
	docker-compose build --pull
	docker-compose run --rm worker memorious upgrade

rebuild:
	docker-compose build --pull --no-cache
	docker-compose run --rm worker memorious upgrade

shell:
	docker-compose run --rm worker /bin/bash