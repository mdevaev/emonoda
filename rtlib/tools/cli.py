# -*- coding: UTF-8 -*-
#
#    rtfetch -- Update rtorrent files from popular trackers
#    Copyright (C) 2012  Devaev Maxim <mdevaev@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####


import sys
import traceback


##### Public methods #####
def oneLine(text, short_flag = True, output = sys.stdout, static_list = [""]) : # pylint: disable=W0102
	old_text = static_list[0]
	if short_flag :
		static_list[0] = text
		text = " "*len(old_text) + "\r" + text + "\r"
	else :
		if len(static_list[0]) != 0 :
			text = " "*len(old_text) + "\r" + text + "\n"
		else :
			text += "\n"
		static_list[0] = ""
	output.write(text)
	output.flush()

def printTraceback(prefix = "", output = sys.stdout) :
	for row in traceback.format_exc().strip().split("\n") :
		print >> output, prefix + row

