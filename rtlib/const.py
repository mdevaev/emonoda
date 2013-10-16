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


##### Public constants #####
VERSION_TUPLE = (0, 3)
VERSION = ".".join(map(str, VERSION_TUPLE))

UPSTREAM_URL = "https://github.com/mdevaev/rtfetch"
RAW_UPSTREAM_URL = "https://raw.github.com/mdevaev/rtfetch/master"

BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"
CLIENT_USER_AGENT = "rtorrent/0.9.2/0.13.2"


###
DEFAULT_TIMEOUT = 5


