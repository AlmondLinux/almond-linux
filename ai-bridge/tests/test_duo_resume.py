"""Regression checks for resume diffs, spent round limits and commit guards."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import bridge
import duo


class Resume(unittest.TestCase):
    def test_saved_base_survives_new_commits(self):
        with tempfile.TemporaryDirectory() as repo:
            def git(*args, check=False):
                return bridge.run(['git', *args], cwd=repo, check=check)
            git('init', '-q', check=True)
            git('config', 'user.name', 'Test', check=True)
            git('config', 'user.email', 'test@example.invalid', check=True)
            path = os.path.join(repo, 'proof.txt')
            with open(path, 'w') as f:
                f.write('initial\n')
            git('add', '.', check=True)
            git('commit', '-qm', 'initial', check=True)
            with mock.patch.object(bridge, 'git', git):
                base = duo.review_base({})
                with open(path, 'a') as f:
                    f.write('first implementation\n')
                git('commit', '-qam', 'implementation', check=True)
                self.assertEqual(duo.review_base({'duo_base': base}), base)
                self.assertIn('first implementation', git('diff', base + '...HEAD').stdout)

    def test_exhausted_limit_stops_before_implementation(self):
        task = {'id': 'T-9000', 'review_round': 2, 'max_review_rounds': 2}
        with mock.patch.object(bridge, 'find_task', return_value=task), \
                mock.patch.object(duo, 'step_implement') as implement:
            with self.assertRaises(duo.DuoError):
                duo.implement_rounds({'limits': {'max_review_rounds': 2}}, 'T-9000',
                                     'claude', 'codex', {}, 'main')
            implement.assert_not_called()

    def test_secret_scan_stops_before_staging(self):
        with mock.patch.object(bridge, 'tracked_files', return_value=['bad.txt']), \
                mock.patch.object(bridge, 'check_secrets', return_value=('fail', 'bad.txt')), \
                mock.patch.object(bridge, 'git') as git:
            with self.assertRaises(duo.DuoError):
                duo.commit_all('must not commit')
            git.assert_not_called()


if __name__ == '__main__':
    unittest.main()
