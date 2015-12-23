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
import os
import socket
import xmlrpc.client
import time
import argparse


# =====
def print_stat(client_url, host, interval):
    server = xmlrpc.client.ServerProxy(client_url)
    while True:
        multicall = xmlrpc.client.MultiCall(server)
        multicall.get_down_rate()  # Download rate
        multicall.get_download_rate()  # Download rate limit
        multicall.get_down_total()  # Downloaded
        multicall.get_up_rate()  # Upload rate
        multicall.get_upload_rate()  # Upload rate limit
        multicall.get_up_total()  # Uploaded
        multicall.dht_statistics()
        values = tuple(multicall())

        for (key, value) in (
            ("gauge-dn_rate",       values[0]),
            ("gauge-dn_rate_limit", values[1]),
            ("bytes-dn_total",      values[2]),
            ("gauge-up_rate",       values[3]),
            ("gauge-up_rate_limit", values[4]),
            ("bytes-up_total",      values[5]),

            ("gauge-dht_active",           values[6]["active"]),
            ("count-dht_nodes",            values[6]["nodes"]),
            ("count-dht_cycle",            values[6]["cycle"]),
            ("count-dht_torrents",         values[6]["torrents"]),
            ("count-dht_buckets",          values[6]["buckets"]),
            ("count-dht_replies_received", values[6]["replies_received"]),
            ("count-dht_peers",            values[6]["peers"]),
            ("count-dht_peers_max",        values[6]["peers_max"]),
            ("count-dht_errors_caught",    values[6]["errors_caught"]),
            ("count-dht_errors_received",  values[6]["errors_received"]),
            ("count-dht_queries_sent",     values[6]["queries_sent"]),
            ("count-dht_queries_received", values[6]["queries_received"]),
            ("bytes-dht_bytes_written",    values[6]["bytes_written"]),
            ("bytes-dht_bytes_read",       values[6]["bytes_read"]),
        ):
            print("PUTVAL {}/rtorrent/{} interval={} N:{}".format(host, key, interval, value), flush=True)
        time.sleep(interval)


# ===== Main =====
def main():
    args_parser = argparse.ArgumentParser(description="Prints collectd stat in plaintext protocol")
    args_parser.add_argument("-n", "--host", default=os.getenv("COLLECTD_HOSTNAME", "localhost"), metavar="<seconds>")
    args_parser.add_argument("-i", "--interval", default=os.getenv("COLLECTD_INTERVAL", 60), type=float, metavar="<seconds>")
    args_parser.add_argument("-t", "--timeout", default=5.0, type=float, metavar="<seconds>")
    args_parser.add_argument("--client-url", default="http://localhost/RPC2", metavar="<url>")

    options = args_parser.parse_args(sys.argv[1:])
    socket.setdefaulttimeout(options.timeout)
    try:
        print_stat(
            client_url=options.client_url,
            host=options.host,
            interval=options.interval,
        )
    except (SystemExit, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()  # Do the thing!
