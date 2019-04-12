.PHONY: clean test package test publish_release

clean:
	rm -rf dist/*

test:
	pytest tests

coverage:
	coverage run --source runway -m pytest
	coverage report
	coverage html

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
