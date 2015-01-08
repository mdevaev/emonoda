#!/usr/bin/env python3


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
    for count in range(len(hashes)):
        for (index, (is_enabled, url)) in enumerate(trackers[count]):
            for (pattern, action) in actions.items():
                if pattern in url and action != is_enabled:
                    multicall.t.set_enabled(hashes[count], index, action)
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
