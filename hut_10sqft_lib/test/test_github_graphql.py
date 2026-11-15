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
import unittest
from unittest.mock import MagicMock, patch

from hut_10sqft_lib.github_graphql import graphql_query


class TestGithubGraphQL(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_graphql_query_success(self, mock_urlopen):
        _TEST_RESPONSE = {"data": {"viewer": {"login": "130s"}}}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            _TEST_RESPONSE
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = graphql_query(
            "query { viewer { login } }", token="dummy-token"
        )
        self.assertEqual(result, _TEST_RESPONSE["data"])

    @patch("urllib.request.urlopen")
    def test_graphql_query_graphql_error(self, mock_urlopen):
        _TEST_RESPONSE = {"errors": [{"message": "Field not found"}]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            _TEST_RESPONSE
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with self.assertRaises(RuntimeError):
            graphql_query("query { badField }", token="dummy-token")

    def test_graphql_query_missing_token(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                graphql_query("query { viewer }")

    @patch("urllib.request.urlopen")
    def test_graphql_query_timeout_passed(self, mock_urlopen):
        _TEST_TIMEOUT = 45.0
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": {}}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        graphql_query("query { test }", token="dummy", timeout=_TEST_TIMEOUT)
        self.assertEqual(mock_urlopen.call_args.kwargs.get("timeout"), _TEST_TIMEOUT)

    @patch("urllib.request.urlopen")
    def test_graphql_query_http_error_converted_to_runtime_error(self, mock_urlopen):
        import io
        import urllib.error
        err_fp = io.BytesIO(b'{"message": "Bad credentials"}')
        http_err = urllib.error.HTTPError(
            url="https://api.github.com/graphql",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=err_fp,
        )
        mock_urlopen.side_effect = http_err

        with self.assertRaises(RuntimeError) as ctx:
            graphql_query("query { test }", token="invalid-token")
        self.assertIn("HTTP Error 401: Unauthorized", str(ctx.exception))
        self.assertIs(ctx.exception.__cause__, http_err)


if __name__ == "__main__":
    unittest.main()
