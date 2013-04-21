# -*- coding: utf-8 -*-


##### Public methods #####
def utf8(line) :
	# XXX: are we 100% sure, that str(line) produces correct utf-8 ? As far as
	# I remember, we already have already seen some issues with koi8r-based
	# descriptions.
	return ( line.encode("utf-8") if type(line) == unicode else str(line) )

def fromUtf8(line) :
	return ( line.decode("utf-8") if type(line) == str else unicode(line) )

def replaceStrInvalids(line) :
	return ( line.decode("utf-8", "replace").encode("utf-8") if type(line) == str else line )

