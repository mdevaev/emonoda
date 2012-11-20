all :
	true

clean :
	find . -type f -name '*.pyc' -exec rm '{}' \;
	rm -rf pkg-root.arch

