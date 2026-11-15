# Copyright 2026 Kinu Garage Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def graphql_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    endpoint: str = "https://api.github.com/graphql",
    user_agent: str = "Hut10sqftAutomation",
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Execute a GitHub GraphQL query and return the data field.

    Raises RuntimeError on GraphQL error or HTTPError.
    """
    auth_token = (
        token
        or os.getenv("PROJECT_AUTOMATION_TOKEN")
        or os.getenv("ADD_TO_PROJECT_PAT_FINEGRAINED")
        or os.getenv("GITHUB_TOKEN")
    )
    if not auth_token:
        raise ValueError(
            "Authentication token missing. Set GITHUB_TOKEN or pass token argument."
        )

    req = urllib.request.Request(
        endpoint,
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if "errors" in res:
                raise RuntimeError(f"GraphQL errors: {res['errors']}")
            return res.get("data", {})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        msg = f"HTTP Error {e.code}: {e.reason}\nResponse: {error_body}"
        print(msg, file=sys.stderr)
        raise RuntimeError(msg) from e
