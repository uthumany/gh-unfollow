"""Tests for gh-unfollow CLI tool."""
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import main


class TestTokenResolution(unittest.TestCase):
    """Test token resolution from various sources."""

    def test_cli_arg_priority(self):
        """--token flag should take highest priority."""
        os.environ.pop("GITHUB_TOKEN", None)
        with patch("sys.exit"):
            token = main.read_token("ghp_test123")
        self.assertEqual(token, "ghp_test123")

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_envtoken"})
    def test_env_var(self):
        """GITHUB_TOKEN env var should work when no CLI arg."""
        with patch("sys.exit"):
            token = main.read_token(None)
        self.assertEqual(token, "ghp_envtoken")

    def test_no_token_found(self):
        """Should exit when no token is available."""
        os.environ.pop("GITHUB_TOKEN", None)
        with patch("sys.exit") as mock_exit:
            main.read_token(None)
            mock_exit.assert_called_once_with(1)


class TestEstimateTime(unittest.TestCase):
    """Test time estimation formatting."""

    def test_seconds(self):
        result = main._estimate_time(10, 2.0, 30, 60)
        self.assertIn("s", result)

    def test_minutes(self):
        result = main._estimate_time(100, 2.0, 30, 60)
        self.assertIn("m", result)

    def test_hours(self):
        result = main._estimate_time(2000, 2.0, 30, 60)
        self.assertIn("h", result)

    def test_dry_run_no_time(self):
        result = main._estimate_time(0, 2.0, 30, 60)
        self.assertIn("s", result)


class TestLogging(unittest.TestCase):
    """Test log function."""

    def test_log_stdout(self):
        captured = StringIO()
        sys.stdout = captured
        main.log("test message")
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("test message", output)

    def test_log_timestamp(self):
        captured = StringIO()
        sys.stdout = captured
        main.log("timestamp test")
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("timestamp test", output)


class TestArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_defaults(self):
        with patch.object(sys, "argv", ["gh-unfollow"]):
            args = main.parse_args()
        self.assertEqual(args.count, 100)
        self.assertEqual(args.delay, 2.0)
        self.assertEqual(args.batch, 30)
        self.assertEqual(args.batch_delay, 60)
        self.assertFalse(args.dry_run)
        self.assertIsNone(args.token)

    def test_custom_values(self):
        with patch.object(
            sys, "argv", ["gh-unfollow", "-n", "500", "--delay", "1.5", "--dry-run"]
        ):
            args = main.parse_args()
        self.assertEqual(args.count, 500)
        self.assertEqual(args.delay, 1.5)
        self.assertTrue(args.dry_run)

    def test_count_zero_means_all(self):
        with patch.object(sys, "argv", ["gh-unfollow", "-n", "0"]):
            args = main.parse_args()
        self.assertEqual(args.count, 0)

    def test_token_flag(self):
        with patch.object(sys, "argv", ["gh-unfollow", "--token", "ghp_testtoken123"]):
            args = main.parse_args()
        self.assertEqual(args.token, "ghp_testtoken123")


class TestAPIMocking(unittest.TestCase):
    """Test API interaction with mocked responses."""

    @patch("main.api_request")
    def test_fetch_following_page(self, mock_api):
        mock_api.return_value = (200, "4999", b'[{"login":"testuser1"},{"login":"testuser2"}]')
        users = main.fetch_following_page("fake_token", 1)
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]["login"], "testuser1")

    @patch("main.api_request")
    def test_unfollow_user_success(self, mock_api):
        mock_api.return_value = (204, "4998", b"")
        code, rem = main.unfollow_user("fake_token", "testuser")
        self.assertEqual(code, 204)

    @patch("main.api_request")
    def test_unfollow_user_404(self, mock_api):
        """404 means already not following — not an error."""
        mock_api.return_value = (404, "4997", b"")
        code, rem = main.unfollow_user("fake_token", "testuser")
        self.assertEqual(code, 404)

    @patch("main.api_request")
    def test_unfollow_user_403(self, mock_api):
        """403 means rate limited — handled by retry logic."""
        mock_api.return_value = (403, "0", b"")
        code, rem = main.unfollow_user("fake_token", "testuser")
        self.assertEqual(code, 403)


if __name__ == "__main__":
    unittest.main()
