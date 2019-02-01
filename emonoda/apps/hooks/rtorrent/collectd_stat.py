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
import operator
import math
import time
import argparse

from typing import List
from typing import Dict


# =====
def get_summary(server: xmlrpc.client.ServerProxy, hashes: List[str]) -> Dict[str, int]:
    mapping = (
        ("peers_accounted",  "leechers"),
        ("is_hash_checking", "is_checking"),
        ("completed_chunks", "completed_chunks"),
        ("chunks_hashed",    "hashed_chunks"),
        ("size_chunks",      "size_chunks"),
        ("message",          "msg"),
    )
    mc = xmlrpc.client.MultiCall(server)
    for torrent_hash in hashes:
        for (method_name, _) in mapping:
            getattr(mc.d, method_name)(torrent_hash)
    rows = list(mc())
    rows = list(
        dict(zip(map(operator.itemgetter(1), mapping), rows[count:count + len(mapping)]))
        for count in range(0, len(rows), len(mapping))
    )

    summary = dict.fromkeys(["total", "dn", "up", "errors"], 0)
    for row in rows:
        if row["leechers"]:
            summary["up"] += 1
        chunks_processing = (row["completed_chunks"] if row["is_checking"] else row["hashed_chunks"])
        done = math.floor(chunks_processing / row["size_chunks"] * 1000)
        if done != 1000:
            summary["dn"] += 1
        if len(row["msg"]) and row["msg"] != "Tracker: [Tried all trackers.]":
            summary["errors"] += 1
    summary["total"] = len(hashes)
    return summary


def print_stat(client_url: str, host: str, interval: float, with_dht: bool, with_summary: bool) -> None:
    server = xmlrpc.client.ServerProxy(client_url)
    while True:
        mc = xmlrpc.client.MultiCall(server)
        mc.throttle.global_down.rate()  # Download rate
        mc.throttle.global_down.max_rate()  # Download rate limit
        mc.throttle.global_down.total()  # Downloaded
        mc.throttle.global_up.rate()  # Upload rate
        mc.throttle.global_up.max_rate()  # Upload rate limit
        mc.throttle.global_up.total()  # Uploaded
        mc.dht.statistics()
        mc.download_list()
        values = list(mc())

        metrics = [
            ("gauge-dn_rate",       values[0]),
            ("gauge-dn_rate_limit", values[1]),
            ("bytes-dn_total",      values[2]),
            ("gauge-up_rate",       values[3]),
            ("gauge-up_rate_limit", values[4]),
            ("bytes-up_total",      values[5]),
        ]
        if with_dht:
            metrics += [
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
            ]
        if with_summary:
            summary = get_summary(server, values[7])
            metrics += [
                ("count-summary_total",  summary["total"]),
                ("count-summary_dn",     summary["dn"]),
                ("count-summary_up",     summary["up"]),
                ("count-summary_errors", summary["errors"]),
            ]

        for (key, value) in metrics:
            print("PUTVAL {}/rtorrent/{} interval={} N:{}".format(host, key, interval, value), flush=True)
        time.sleep(interval)


# ===== Main =====
def main() -> None:
    args_parser = argparse.ArgumentParser(description="Prints collectd stat in plaintext protocol")
    args_parser.add_argument("--with-dht", action="store_true")
    args_parser.add_argument("--with-summary", action="store_true")
    args_parser.add_argument("-n", "--host", default=os.getenv("COLLECTD_HOSTNAME", "localhost"), metavar="<hostname>")
    args_parser.add_argument("-i", "--interval", default=os.getenv("COLLECTD_INTERVAL", "60"), type=float, metavar="<seconds>")
    args_parser.add_argument("-t", "--timeout", default=5.0, type=float, metavar="<seconds>")
    args_parser.add_argument("--client-url", default="http://localhost/RPC2", metavar="<url>")

    options = args_parser.parse_args(sys.argv[1:])
    socket.setdefaulttimeout(options.timeout)
    try:
        print_stat(
            client_url=options.client_url,
            host=options.host,
            interval=options.interval,
            with_dht=options.with_dht,
            with_summary=options.with_summary,
        )
    except (SystemExit, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()  # Do the thing!
