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
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_graphql_query_retry_on_504_success(self, mock_urlopen, mock_sleep):
        import io
        import urllib.error

        err_fp = io.BytesIO(b"<!DOCTYPE html><html>Gateway Timeout</html>")
        http_504 = urllib.error.HTTPError(
            url="https://api.github.com/graphql",
            code=504,
            msg="Gateway Timeout",
            hdrs={},
            fp=err_fp,
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": {"result": "ok"}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.side_effect = [http_504, mock_resp]

        res = graphql_query("query { test }", token="dummy-token", retries=2, backoff_factor=0.5)
        self.assertEqual(res, {"result": "ok"})
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_graphql_query_retry_exhaustion_on_504(self, mock_urlopen, mock_sleep):
        import io
        import urllib.error

        def make_504():
            err_fp = io.BytesIO(b"Gateway Timeout")
            return urllib.error.HTTPError(
                url="https://api.github.com/graphql",
                code=504,
                msg="Gateway Timeout",
                hdrs={},
                fp=err_fp,
            )

        mock_urlopen.side_effect = [make_504(), make_504(), make_504()]

        with self.assertRaises(RuntimeError) as ctx:
            graphql_query("query { test }", token="dummy-token", retries=2, backoff_factor=1.0)
        self.assertIn("HTTP Error 504: Gateway Timeout", str(ctx.exception))
        self.assertEqual(mock_urlopen.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_graphql_query_retry_on_network_timeout(self, mock_urlopen, mock_sleep):
        timeout_err = TimeoutError("The read operation timed out")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": {"status": "recovered"}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.side_effect = [timeout_err, mock_resp]

        res = graphql_query("query { test }", token="dummy-token", retries=2, backoff_factor=1.0)
        self.assertEqual(res, {"status": "recovered"})
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_graphql_query_retry_after_header(self, mock_urlopen, mock_sleep):
        import io
        import urllib.error

        err_fp = io.BytesIO(b"Rate limit exceeded")
        http_429 = urllib.error.HTTPError(
            url="https://api.github.com/graphql",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "5"},
            fp=err_fp,
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": {"status": "ok"}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.side_effect = [http_429, mock_resp]

        res = graphql_query("query { test }", token="dummy-token", retries=1)
        self.assertEqual(res, {"status": "ok"})
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(5.0)


if __name__ == "__main__":
    unittest.main()
