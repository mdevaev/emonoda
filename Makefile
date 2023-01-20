all: bencoder

bencoder:
	python3 setup.py build_ext --inplace

regen: regen-trackers

regen-trackers: bencoder
	python3 -c 'from json import dumps; from emonoda.plugins import get_classes; \
			[ open("trackers/{}.json".format(name), "w").write(dumps(cls._get_local_info(), sort_keys=True, indent=" " * 4)) \
			for (name, cls) in get_classes("trackers").items() ]'

release:
	make clean
	make tox
	make clean
	make push
	make bump
	make push
#	make pypi
	make clean
	make mkdocs
	make clean
	make mkdocs-release
	make clean

tox:
	tox -q $(if $(E),-e $(E),-p auto)

bump:
	bumpversion patch

push:
	git push
	git push --tags

mkdocs:
	mkdocs build

mkdocs-release:
	mkdocs gh-deploy

pypi:
	python3 setup.py register
	python3 setup.py sdist
	twine upload dist/*

clean:
	rm -rf build site dist pkg src *.egg-info emonoda-*.tar.gz
	rm -f emonoda/thirdparty/bencoder.c emonoda/thirdparty/bencoder.*.so
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox .mypy_cache
