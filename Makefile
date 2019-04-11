.PHONY: clean test package test publish_release

clean:
	rm -rf dist/*

test:
	py.test tests

package:
	python setup.py sdist
	python setup.py bdist_wheel

dev:
	pip install -e .
	pip install -r requirements-dev.txt

publish_release:
	rm -rf dist/*	
	python setup.py tag_release
	git push --tags
	make package
	twine upload dist/*
