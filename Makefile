.PHONY: clean test package dev clean_package clean_docs docs publish_release

clean: clean_docs clean_package

test:
	py.test tests

package:
	python setup.py sdist
	python setup.py bdist_wheel

dev:
	pip install -e .
	pip install -r requirements-dev.txt

clean_package:
	rm -rf dist/*

clean_docs:
	$(MAKE) -C docs clean

docs:
	$(MAKE) -C docs html

publish_release:
	rm -rf dist/*
	python setup.py tag_release
	git push --tags
	make package
	twine upload dist/*
