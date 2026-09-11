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


import urllib.request
import json

from typing import List
from typing import Dict
from typing import NamedTuple
from typing import Optional
from typing import Any

from . import read_url
from . import build_opener


# =====
class FlareSolverrError(Exception):
    pass


class Solution(NamedTuple):
    url: str
    status: int
    html: str
    user_agent: str
    cookies: List[Dict[str, Any]]


def solve(
    endpoint: str,
    url: str,
    timeout: float=60.0,
    opener: Optional[urllib.request.OpenerDirector]=None,
) -> Solution:

    # FlareSolverr is the egress here, so it must be reached directly -- never through
    # the tracker's own proxy_url. Use a plain opener unless the caller passes one.
    if opener is None:
        opener = build_opener()

    request = {
        "cmd":        "request.get",
        "url":        url,
        "maxTimeout": int(timeout * 1000),
    }
    try:
        raw = read_url(
            opener=opener,
            url=endpoint.rstrip("/") + "/v1",
            data=json.dumps(request).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            timeout=timeout + 10.0,  # give FlareSolverr its full maxTimeout before we give up
        )
        response = json.loads(raw.decode("utf-8"))
    except Exception as err:
        raise FlareSolverrError(f"FlareSolverr request failed: {type(err).__name__}: {err}")

    if response.get("status") != "ok":
        raise FlareSolverrError(f"FlareSolverr couldn't solve {url!r}: {response.get('message')!r}")

    solution = response.get("solution", {})
    return Solution(
        url=solution.get("url", url),
        status=int(solution.get("status", 0)),
        html=solution.get("response", ""),
        user_agent=solution.get("userAgent", ""),
        cookies=list(solution.get("cookies", [])),
    )
