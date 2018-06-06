all: bencoder

bencoder:
	python setup.py build_ext --inplace

regen: regen-trackers

regen-trackers: bencoder
	python -c 'from json import dumps; from emonoda.plugins import get_classes; \
			[ open("trackers/{}.json".format(name), "w").write(dumps(cls._get_local_info(), sort_keys=True, indent=" " * 4)) \
			for (name, cls) in get_classes("trackers").items() ]'

release:
	make clean
	make tox
	make clean
	make push
	make bump
	make push
	# make mkdocs
	make pypi
	make clean

tox:
	tox

bump:
	bumpversion patch

push:
	git push
	git push --tags

mkdocs:
	mkdocs build

pypi:
	python setup.py register
	python setup.py sdist upload
	# python setup.py upload_docs --upload-dir=site

clean:
	rm -rf build site dist pkg src *.egg-info emonoda-*.tar.gz
	rm -f emonoda/thirdparty/bencoder.c emonoda/thirdparty/bencoder.*.so
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox .mypy_cache
