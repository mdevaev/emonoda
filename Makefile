all :
	true

install :
	mkdir -p $(DESTDIR)/usr/bin
	install -m 755 rtfetch.py $(DESTDIR)/usr/bin/rtfetch

