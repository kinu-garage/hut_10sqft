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
import time
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
    retries: int = 3,
    backoff_factor: float = 1.0,
) -> Dict[str, Any]:
    """Execute a GitHub GraphQL query and return the data field.

    Retries on transient HTTP status codes (429, 500, 502, 503, 504)
    and network connection / timeout errors.
    Raises RuntimeError on GraphQL error or when retries are exhausted.
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

    transient_http_codes = {429, 500, 502, 503, 504}
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if "errors" in res:
                    raise RuntimeError(f"GraphQL errors: {res['errors']}")
                return res.get("data", {})
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            msg = f"HTTP Error {e.code}: {e.reason}\nResponse: {error_body}"
            if e.code in transient_http_codes and attempt < retries:
                attempt += 1
                retry_after_hdr = getattr(e, "headers", None)
                retry_after_val = (
                    retry_after_hdr.get("Retry-After")
                    if retry_after_hdr and hasattr(retry_after_hdr, "get")
                    else None
                )
                try:
                    sleep_time = (
                        float(retry_after_val)
                        if retry_after_val is not None
                        else backoff_factor * (2 ** (attempt - 1))
                    )
                except (ValueError, TypeError):
                    sleep_time = backoff_factor * (2 ** (attempt - 1))
                print(
                    f"Transient HTTP {e.code} error from GitHub GraphQL API. "
                    f"Retrying in {sleep_time:.1f}s (attempt {attempt}/{retries})...",
                    file=sys.stderr,
                )
                time.sleep(sleep_time)
                continue
            print(msg, file=sys.stderr)
            raise RuntimeError(msg) from e
        except (urllib.error.URLError, TimeoutError) as e:
            msg = f"Network or timeout error contacting GitHub GraphQL API: {e}"
            if attempt < retries:
                attempt += 1
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                print(
                    f"{msg}. Retrying in {sleep_time:.1f}s (attempt {attempt}/{retries})...",
                    file=sys.stderr,
                )
                time.sleep(sleep_time)
                continue
            print(msg, file=sys.stderr)
            raise RuntimeError(msg) from e
