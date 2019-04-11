.PHONY: clean test package test

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
