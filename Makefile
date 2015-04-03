all:
	true

regen: regen-fetchers

regen-fetchers:
	python -c '\
			import json, emonoda.plugins; \
			print(json.dumps({ \
				item.get_name(): { \
					"version": item.get_version(), \
					"fingerprint": item.get_fingerprint(), \
				} \
				for item in emonoda.plugins._get_classes()["fetchers"].values() \
			}, sort_keys=True, indent=" " * 4)) \
		' > fetchers.json

release:
	make tox
	make push
	make bump
	make push
	make pypi
	make aur
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

aur:
	mkaurball -f
	burp -c network emonoda-*.src.tar.gz

clean:
	rm -rf build dist pkg src *.egg-info emonoda-*.tar.gz
	find -name __pycache__ | xargs rm -rf

clean-all: clean
	rm -rf .tox
