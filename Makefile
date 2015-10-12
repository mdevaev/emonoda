all:
	true

regen: regen-fetchers

regen-fetchers:
	python -c 'from json import dumps; from emonoda.plugins import _get_classes; \
			[ open("fetchers/{}.json".format(name), "w").write(dumps(cls._get_local_info(), sort_keys=True, indent=" " * 4)) \
			for (name, cls) in _get_classes()["fetchers"].items() ]'

release:
	make tox
	make push
	make bump
	make push
	make pypi
	make clean

tox:
	tox

bump:
	bumpversion patch

push:
	git push
	git push --tags

pypi:
	python setup.py register
	python setup.py sdist upload

clean:
	rm -rf build dist pkg src *.egg-info emonoda-*.tar.gz
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox
