all:
	true

pypi:
	python setup.py register
	python setup.py sdist upload

clean:
	rm -rf build dist *.egg-info
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox
