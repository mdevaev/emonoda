all :
	true

regen : regen-fetchers

regen-fetchers :
	python2 -c '\
			import json, rtlib.fetchers; \
			print json.dumps(dict([ \
					( item.plugin(), { \
							"version" : item.version(), \
							"path" : item.__module__.replace(".", "/") + ".py", \
						} ) \
					for item in rtlib.fetchers.FETCHERS_MAP.values() \
				])) \
		' > fetchers.json

pylint :
	pylint --rcfile=pylint.ini \
		rtlib \
		*.py \
		--output-format=colorized 2>&1 | less -SR

clean :
	find . -type f -name '*.pyc' -exec rm '{}' \;
	rm -rf pkg-root.arch pkg src build rtfetch.egg-info

