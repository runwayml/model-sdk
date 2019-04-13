.PHONY: clean test test-debug coverage coverage-codecov package dev clean-package clean-docs clean-coverage docs publish-release

clean: clean-docs clean-package clean-coverage

test:
	pytest tests

test-debug:
	pytest tests -s

coverage:
	pytest --cov-report html --cov runway --disable-warnings tests
	pytest --cov-report term --cov runway --disable-warnings tests

coverage-codecov:
	pytest --cov-report xml --cov runway tests

package:
	python setup.py sdist
	python setup.py bdist_wheel

dev:
	pip install -e .
	pip install -r requirements-dev.txt

clean-package:
	rm -rf dist/*

clean-docs:
	$(MAKE) -C docs clean

clean-coverage:
	rm -f .coverage
	rm -f coverage.xml
	rm -rf htmlcov

docs:
	$(MAKE) -C docs html

publish-release: clean-package
	python setup.py tag_release
	git push --tags
	make package
	twine upload dist/*
