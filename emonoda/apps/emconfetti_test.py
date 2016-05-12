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
import json
import shutil
import contextlib
import traceback
import threading
import operator
import argparse

from ..plugins.trackers import TrackerError
from ..plugins.trackers import WithCheckHash
from ..plugins.trackers import WithCheckScrape
from ..plugins.trackers import WithCheckTime

from ..helpers import tcollection
from ..helpers import surprise

from .. import tfile
from .. import fmt
from .. import tools

from . import init
from . import get_configured_log
from . import get_configured_client
from . import get_configured_trackers
from . import get_configured_confetti

class Torrent:
    def get_comment(self):
        return "Test, test, test"

class Tracker:
    PLUGIN_NAME = "TEST.org.ru"

def main():
    (parent_parser, argv, config) = init()
    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:
            results = {
                "affected":{
                    "test.torrent":{
                        "diff":{
                            "added": ["nya.mkv", "nya.srt"],
                            "removed": ["nyaa.srt", "nyaa.mkv"],
                            "modified": [],
                            "type_modified": ["list.lst"]
                        },
                        "torrent": Torrent(), "tracker":Tracker()
                    },
                    "test1.torrent":{
                        "diff":{
                            "added": ["nya.mkv", "nya.srt"],
                            "removed": ["nyaa.srt", "nyaa.mkv"],
                            "modified": [],
                            "type_modified": ["list.lst"]
                        },
                        "torrent": Torrent(), "tracker":Tracker()
                    }
                },
                "passed":{},
                "not_in_client":{},
                "unknown":{},
                "invalid":{},
                "tracker_error": {},
                "unhandled_error": {}
            }
            confetti = get_configured_confetti(
                config=config,
                log=log_stderr,
            )
            surprise.deploy_surprise(
                    source="emupdate",
                    results=results,
                    confetti=confetti,
                    log=log_stderr,
            )

if __name__ == "__main__":
    main()
