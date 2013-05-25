# -*- coding: utf-8 -*-


import math


##### Public constants #####
UNITS_LIST = zip(
	("bytes", "kB", "MB", "GB", "TB", "PB"),
	(0, 0, 1, 2, 2, 2),
)


##### Public methods #####
def formatSize(size) :
	if size > 1 :
		exponent = min(int(math.log(size, 1024)), len(UNITS_LIST) - 1)
		quotient = float(size) / 1024 ** exponent
		(unit, decimals) = UNITS_LIST[exponent]
		result = ("{:.%sf} {}" % (decimals)).format(quotient, unit)
	elif size == 0 :
		result = "0 bytes"
	elif size == 1 :
		result = "1 byte"
	else :
		ValueError("size must be >= 0")
	return result

def formatProgress(value, limit) :
	return (("%%%dd/" % (len(str(limit)))) + "%d") % (value, limit)

