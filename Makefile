.PHONY: clean test package dev clean-package clean-docs docs publish-release

clean: clean-docs clean-package

test:
	py.test tests

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

docs:
	$(MAKE) -C docs html

publish-release: clean-package
	python setup.py tag_release
	git push --tags
	make package
	twine upload dist/*
