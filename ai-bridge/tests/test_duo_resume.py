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

from test_duo import Sandbox, plan, review


class Recovery(Sandbox):
    def exercise(self, result, commit_error=None):
        with mock.patch.object(duo, 'step_implement', return_value=({'summary': 'x', 'files_changed': [],
                    'tests_run': [], 'not_done': [], 'notes_for_reviewer': ''}, None)) as implement, \
                mock.patch.object(bridge, 'run_checks', return_value=[{'name': 'test', 'status': 'pass', 'detail': ''}]), \
                mock.patch.object(duo, 'commit_all', side_effect=commit_error), \
                mock.patch.object(duo, 'step_review', return_value=(result, None)), \
                mock.patch.object(duo, 'say') as say:
            outcome = duo.implement_rounds(self.cfg, self.tid, 'claude', 'codex', plan(), 'main')
            return outcome, implement, say

    def test_approval_with_unverified_claims_needs_owner(self):
        r = review('approve'); r['status_claims_ok'] = False
        self.assertEqual(self.exercise(r)[0][0], 'needs-owner')

    def test_approval_with_honesty_issue_needs_owner(self):
        r = review('approve'); r['honesty_issues'] = ['not measured']
        self.assertEqual(self.exercise(r)[0][0], 'needs-owner')

    def test_approval_with_question_needs_owner(self):
        r = review('approve'); r['questions_for_owner'] = ['Choose a direction']
        self.assertEqual(self.exercise(r)[0][0], 'needs-owner')

    def test_commit_block_records_needs_owner(self):
        with self.assertRaises(duo.DuoError):
            self.exercise(review('approve'), duo.DuoError('Secret scan blocked the commit'))
        task = bridge.find_task(self.tid)
        self.assertEqual(task['status'], 'needs-owner')
        self.assertIn('automatic commit blocked', task['_body'])
        self.assertEqual(task['review_round'], 0)

    def test_resume_supplies_last_findings_and_failed_checks(self):
        r = review('request_changes')
        r['summary'] = 'Fix the previous implementation'
        bridge.record_review(bridge.find_task(self.tid), r, 'test')
        task = bridge.find_task(self.tid)
        task['duo_failed_checks'] = 'Shell syntax'
        task['duo_base'] = 'a' * 40
        bridge.save_task(task)
        outcome, implement, say = self.exercise(review('approve'))
        self.assertEqual(outcome[0], 'approved')
        self.assertEqual(implement.call_args.args[4]['summary'], r['summary'])
        self.assertEqual(implement.call_args.args[5], ['Shell syntax'])
        self.assertTrue(any(c.args[3] == 'implementation round 2' for c in say.call_args_list))
        self.assertEqual(bridge.find_task(self.tid)['duo_base'], 'a' * 40)


class MissingBase(unittest.TestCase):
    def test_missing_base_refuses_without_fallback(self):
        response = mock.Mock(returncode=1, stdout='', stderr='missing')
        with mock.patch.object(bridge, 'git', return_value=response):
            with self.assertRaisesRegex(duo.DuoError, 'unavailable'):
                duo.review_base({'duo_base': 'missing'})

    def test_non_ancestor_base_refuses(self):
        responses = [mock.Mock(returncode=0, stdout='a'*40+'\n'), mock.Mock(returncode=1)]
        with mock.patch.object(bridge, 'git', side_effect=responses):
            with self.assertRaisesRegex(duo.DuoError, 'not an ancestor'):
                duo.review_base({'duo_base': 'a'*40})


class CriticContext(unittest.TestCase):
    def test_saved_critic_reaches_implementation_and_review(self):
        import json
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(duo, 'CONV', tmp), \
                mock.patch.object(duo, 'preamble', return_value=''), \
                mock.patch.object(bridge, 'build_packet', return_value='packet'), \
                mock.patch.object(duo, 'call', return_value=({}, None)) as call:
            body = {'verdict': 'change', 'concerns': ['Keep the agreed scope'],
                    'missing_steps': [], 'implementer_agree': True, 'notes': ''}
            bridge.write(os.path.join(tmp, 'T-9000-plan-review.json'), json.dumps(body))
            task = {'id': 'T-9000'}
            duo.step_implement({}, task, 'claude', {})
            self.assertIn('Keep the agreed scope', call.call_args.args[2])
            duo.step_review({}, task, 'codex', 'main', {}, [])
            self.assertIn('Keep the agreed scope', call.call_args.args[2])


if __name__ == '__main__':
    unittest.main()
