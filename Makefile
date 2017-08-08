all:
	true

regen: regen-trackers

regen-trackers:
	python -c 'from json import dumps; from emonoda.plugins import _get_classes; \
			[ open("trackers/{}.json".format(name), "w").write(dumps(cls._get_local_info(), sort_keys=True, indent=" " * 4)) \
			for (name, cls) in _get_classes()["trackers"].items() ]'

release:
	make tox
	make push
	make bump
	make push
	make mkdocs
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
	python setup.py upload_docs --upload-dir=site

clean:
	rm -rf build site dist pkg src *.egg-info emonoda-*.tar.gz
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox
