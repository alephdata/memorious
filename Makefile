
all: clean test

install: clean 
	set -e; \
	. ./env.sh; \
	pip install -q nose twine; \
	pip install -e . ; \
	if [ -f $$MEMORIOUS_CONFIG_PATH/setup.py ]; \
	then \
		pip install -e $$MEMORIOUS_CONFIG_PATH; \
	fi

test: install
	# nosetests


# To release, run "bumpversion patch" or "bumpversion minor",
# then push the newly created tag.
# release: dists
# 	pip install -q twine
# 	twine upload dist/*
# 
# dists: install
# 	python setup.py sdist
# 	python setup.py bdist_wheel

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