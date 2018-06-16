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


import traceback

from typing import List

from ..cli import Log

from ..plugins.confetti import ResultsType
from ..plugins.confetti import BaseConfetti


# =====
def deploy_surprise(
    source: str,
    results: ResultsType,
    confetti: List[BaseConfetti],
    log: Log,
) -> bool:

    ok = True
    for sender in confetti:
        log.info("Processing confetti {blue}%s{reset} ...", (sender.PLUGIN_NAMES[0],), one_line=True)
        try:
            sender.send_results(source, results)
            log.info("Confetti {blue}%s{reset} {green}processed{reset}", (sender.PLUGIN_NAMES[0],))
        except Exception as err:
            log.error("Can't process {red}%s{reset}: {red}%s{reset}(%s)", (sender.PLUGIN_NAMES[0], type(err).__name__, err))
            log.print("%s", ("\n".join("\t" + row for row in traceback.format_exc().strip().split("\n")),))
            ok = False
    if not ok:
        log.error("One or more confetti failed")
    return ok
