"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import sys
import socket
import xmlrpc.client
import argparse


# =====
def manage_trackers(client_url, to_enable, to_disable):
    server = xmlrpc.client.ServerProxy(client_url)

    multicall = xmlrpc.client.MultiCall(server)
    hashes = server.download_list()
    for t_hash in hashes:
        multicall.t.multicall(t_hash, "", "t.is_enabled=", "t.get_url=")
    trackers = list(multicall())

    actions = dict.fromkeys(set(to_enable or ()), 1)
    actions.update(dict.fromkeys(set(to_disable or ()), 0))

    multicall = xmlrpc.client.MultiCall(server)
    for (count, t_hash) in enumerate(hashes):
        for (index, (is_enabled, url)) in enumerate(trackers[count]):
            for (pattern, action) in actions.items():
                if pattern in url and action != is_enabled:
                    multicall.t.set_enabled(t_hash, index, action)
                    print(url, pattern, action)
                    continue
    multicall()


# ===== Main =====
def main():
    args_parser = argparse.ArgumentParser(description="Manage trackers (rtorrent only)")
    args_parser.add_argument("--enable", nargs="+", metavar="<pattern>")
    args_parser.add_argument("--disable", nargs="+", metavar="<pattern>")
    args_parser.add_argument("-t", "--timeout", default=5.0, type=float, metavar="<seconds>")
    args_parser.add_argument("--client-url", default="http://localhost/RPC2", metavar="<url>")

    options = args_parser.parse_args(sys.argv[1:])
    socket.setdefaulttimeout(options.timeout)
    manage_trackers(
        client_url=options.client_url,
        to_enable=options.enable,
        to_disable=options.disable,
    )


if __name__ == "__main__":
    main()  # Do the thing!
