"""Safety regressions: no real GitHub requests or relationship changes."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src import main


class SafetyTests(unittest.TestCase):
    def test_old_event_is_inactive(self):
        old = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        with patch.object(main, 'check_inactive', return_value=(False, old)):
            self.assertEqual(main.filter_inactive('fake', [{'login': 'old'}], 30, MagicMock()), [{'login': 'old'}])

    def test_activity_error_is_not_inactivity(self):
        with patch.object(main, 'api_request', return_value=(403, '0', b'')):
            self.assertFalse(main.check_inactive('fake', 'user')[0])

    def test_no_events_is_unknown_not_inactive(self):
        with patch.object(main, 'api_request', return_value=(200, '10', b'[]')):
            self.assertFalse(main.check_inactive('fake', 'user')[0])

    def test_following_failure_is_not_end_of_list(self):
        with patch.object(main, 'api_request', return_value=(403, '0', b'')):
            with self.assertRaises(main.APIError):
                main.fetch_following_page('fake', 2)

    def test_followers_failure_is_not_empty_followers(self):
        with patch.object(main, 'api_request', return_value=(403, '0', b'')):
            with self.assertRaises(main.APIError):
                main.fetch_followers('fake', MagicMock())

    def test_invalid_arguments_rejected(self):
        for flags in [['--count', '-1'], ['--batch', '0'], ['--delay', '-1'], ['--delay', 'nan'], ['--delay', 'inf'], ['--inactive-days', '-1'], ['--batch-delay', '-1'], ['--backup', 'a', '--restore', 'b']]:
            with self.subTest(flags=flags), patch.object(sys, 'argv', ['gh-unfollow'] + flags):
                with self.assertRaises(SystemExit) as error:
                    main.parse_args()
                self.assertEqual(error.exception.code, 2)

    def run_cli(self, flags, users, *, followers=None):
        ui = MagicMock()
        ui.is_whitelisted.side_effect = lambda name: name.lower() == 'keep'
        pages = [users[i:i + 100] for i in range(0, len(users), 100)] + [[]]
        with patch.object(sys, 'argv', ['gh-unfollow', '--token', 'fake', '--no-rich'] + flags), patch.object(main, 'UI', return_value=ui), patch.object(main, 'get_user_info', return_value={'login': 'tester', 'following': len(users)}), patch.object(main, 'fetch_following_page', side_effect=[(p, '1000') for p in pages]) as fetch, patch.object(main, 'unfollow_user', return_value=(204, '999')) as unfollow, patch.object(main, 'fetch_followers', return_value=followers or set()), patch.object(main.time, 'sleep'):
            main.main()
        return ui, fetch, unfollow

    def test_count_applies_after_skips(self):
        _, _, unfollow = self.run_cli(['-n', '2'], [{'login': 'keep'}, {'login': 'a'}, {'login': 'b'}])
        self.assertEqual(unfollow.call_count, 2)

    def test_snapshot_fetched_before_any_delete(self):
        events = []
        users = [{'login': f'u{i}'} for i in range(150)]
        with patch.object(main, 'unfollow_user', side_effect=lambda *a: events.append('delete') or (204, '999')):
            # Use separate wiring so call ordering is visible.
            ui = MagicMock()
            ui.is_whitelisted.return_value = False
            with patch.object(sys, 'argv', ['gh-unfollow', '--token', 'fake', '-n', '0']), patch.object(main, 'UI', return_value=ui), patch.object(main, 'get_user_info', return_value={'login': 'tester', 'following': 150}), patch.object(main, 'fetch_following_page', side_effect=lambda token, page: events.append(f'page{page}') or (users[(page-1)*100:page*100], '999')), patch.object(main.time, 'sleep'):
                main.main()
        self.assertLess(events.index('page2'), events.index('delete'))
        self.assertEqual(events.count('delete'), 150)

    def test_restore_dry_run_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'backup.json')
            with open(path, 'w') as stream:
                json.dump({'version': 1, 'users': ['octocat']}, stream)
            with patch.object(sys, 'argv', ['gh-unfollow', '--token', 'fake', '--restore', path, '--dry-run']), patch.object(main, 'UI', return_value=MagicMock()), patch.object(main, 'api_request') as api, patch.object(main.time, 'sleep'):
                main.main()
            api.assert_not_called()

    def test_restore_rejects_invalid_backup_before_writes(self):
        for data in [[], {'users': 'abc'}, {'users': ['safe', '../unsafe']}, {'users': [123]}]:
            with self.subTest(data=data), tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, 'backup.json')
                with open(path, 'w') as stream:
                    json.dump(data, stream)
                with patch.object(main, 'api_request') as api:
                    with self.assertRaises((main.APIError, SystemExit)):
                        main.cmd_restore('fake', path, MagicMock(), 0, 30, 0)
                api.assert_not_called()

    def test_interactive_respects_count_and_pacing(self):
        users = [{'login': 'a'}, {'login': 'b'}, {'login': 'c'}]
        with patch.object(main, 'interactive_select', return_value=users), patch.object(main.time, 'sleep') as sleep:
            # run_cli also patches sleep; assert pacing through cooldown instead.
            ui, _, unfollow = self.run_cli(['--interactive', '-n', '2', '--batch', '1', '--batch-delay', '1'], users)
        self.assertEqual(unfollow.call_count, 2)
        ui.cooldown.assert_called()

    def test_interactive_and_regular_dry_run_same_count(self):
        users = [{'login': 'a'}, {'login': 'b'}, {'login': 'c'}]
        with patch.object(main, 'interactive_select', return_value=users):
            ui, _, unfollow = self.run_cli(['--interactive', '--dry-run', '-n', '1'], users)
        unfollow.assert_not_called()
        self.assertEqual(ui.log_unfollow.call_count, 1)

    def test_non_mutual_comparison_case_insensitive(self):
        _, _, unfollow = self.run_cli(['--non-mutual', '-n', '0'], [{'login': 'Mutual'}, {'login': 'other'}], followers={'mutual'})
        self.assertEqual([call.args[1] for call in unfollow.call_args_list], ['other'])

    def test_failed_backup_does_not_overwrite_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'backup.json')
            with open(path, 'w') as stream:
                stream.write('existing')
            with patch.object(main, 'fetch_following_page', side_effect=main.APIError('read failed')):
                with self.assertRaises(main.APIError):
                    main.cmd_backup('fake', path, MagicMock())
            with open(path) as stream:
                self.assertEqual(stream.read(), 'existing')


class TransportAndRetryTests(unittest.TestCase):
    def test_invalid_user_info_rejected(self):
        for value in [True, -1, '10', None]:
            with self.subTest(value=value), patch.object(main, 'api_request', return_value=(200, '10', json.dumps({'login': 'tester', 'following': value}).encode())):
                with self.assertRaises(main.APIError):
                    main.get_user_info('fake')

    def test_retry_then_success_for_unfollow_and_restore(self):
        for restore in [False, True]:
            for rem in ['0', 0]:
                ui = MagicMock()
                target = 'api_request' if restore else 'unfollow_user'
                responses = [(403, rem, b''), (204, '1000', b'')] if restore else [(403, rem), (204, '1000')]
                with self.subTest(restore=restore, rem=rem), patch.object(main, target, side_effect=responses) as request:
                    self.assertEqual(main.execute_users('fake', [{'login': 'a'}], ui, 0, 30, 0, restore=restore), 1)
                self.assertEqual(request.call_count, 2)
                ui.cooldown.assert_called_once()

    def test_permission_error_never_retried(self):
        with patch.object(main, 'unfollow_user', return_value=(403, '999')) as request:
            with self.assertRaises(main.APIError):
                main.execute_users('fake', [{'login': 'a'}, {'login': 'b'}], MagicMock(), 0, 30, 0)
        self.assertEqual(request.call_count, 1)

    def test_persistent_rate_limit_is_bounded(self):
        with patch.object(main, 'unfollow_user', return_value=(429, '0')) as request:
            with self.assertRaises(main.APIError):
                main.execute_users('fake', [{'login': 'a'}, {'login': 'b'}], MagicMock(), 0, 30, 0)
        self.assertEqual(request.call_count, 3)

    def test_secondary_rate_limit_respects_retry_after(self):
        import urllib.error
        from io import BytesIO
        headers = {'Retry-After': '17', 'X-RateLimit-Remaining': '200'}
        error = urllib.error.HTTPError('https://api.github.com/user/following/a', 403, 'secondary limit', headers, BytesIO(b'{"message":"secondary rate limit"}'))
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 204
        response.headers = {'X-RateLimit-Remaining': '199'}
        response.read.return_value = b''
        ui = MagicMock()
        with patch.object(main.urllib.request, 'urlopen', side_effect=[error, response]) as request:
            self.assertEqual(main.execute_users('fake', [{'login': 'a'}], ui, 0, 30, 0), 1)
        ui.cooldown.assert_called_once_with(17, 'Rate limit — bounded retry')
        self.assertEqual(request.call_count, 2)

    def test_network_error_is_controlled_and_timeout_set(self):
        import urllib.error
        with patch.object(main.urllib.request, 'urlopen', side_effect=urllib.error.URLError('offline')) as request:
            with self.assertRaises(main.APIError):
                main.api_request('fake', 'GET', 'https://api.github.com/user')
        self.assertEqual(request.call_args.kwargs['timeout'], 30)

    def test_no_token_path_is_hermetic_and_noninteractive(self):
        import subprocess
        with patch.dict(os.environ, {}, clear=True), patch.object(main.os.path, 'exists', return_value=False), patch.object(subprocess, 'run', return_value=MagicMock(stdout='')) as run, patch('builtins.print'):
            with self.assertRaises(SystemExit) as error:
                main.read_token()
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(run.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'], '0')


class TerminalTests(unittest.TestCase):
    def test_plain_ui_does_not_disable_other_instances(self):
        from src import ui
        before = ui.Colors.CYAN
        with patch.object(ui, 'RICH_AVAILABLE', False):
            plain = ui.UI(version='test', no_color=True)
            colored = ui.UI(version='test', no_color=False)
        self.assertEqual(plain.colors.CYAN, '')
        self.assertEqual(colored.colors.CYAN, before)
        self.assertEqual(ui.Colors.CYAN, before)


if __name__ == '__main__':
    unittest.main()
