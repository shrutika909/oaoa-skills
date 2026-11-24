import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'selection_state.py'


class SelectionStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'

    def tearDown(self):
        self.temp.cleanup()

    def run_command(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), '--state-dir', str(self.state), *args],
            capture_output=True, text=True,
        )

    def save(self, sevs):
        receipt = self.root / 'discovery.json'
        receipt.write_text(json.dumps({
            'schema': 'oaoa.sev-discovery.v1',
            'generated_at': '2026-11-11T20:00:00+00:00',
            'selected': [{'sev': sev, 'generated_revision_count': 1, 'risk': {
                'verified': True, 'visibility': 'public', 'is_privacy': False,
                'is_security': False, 'is_privacy_safeguard': False,
            }} for sev in sevs],
            'complete': False,
            'verification_failure_count': 0,
        }))
        return self.run_command('save-discovery', '--receipt', str(receipt))

    def load(self, name):
        return json.loads((self.state / name).read_text())

    def test_discovery_is_reusable_and_preserves_coverage_limits(self):
        result = self.save(['S123456', 'S123457'])
        self.assertEqual(result.returncode, 0, result.stderr)
        candidates = self.load('candidates.json')
        self.assertEqual(candidates['sevs'], ['S123456', 'S123457'])
        self.assertEqual(candidates['eligible_sevs'], ['S123456', 'S123457'])
        self.assertFalse(candidates['discovery_complete'])
        self.assertEqual(candidates['verification_failure_count'], 0)
        self.assertEqual((self.state / 'candidates.json').stat().st_mode & 0o777, 0o600)

    def test_outcome_accumulates_skips_without_discarding_prior_records(self):
        self.assertEqual(self.save(['S123456', 'S123457']).returncode, 0)
        for sev, status in [('S123456', 'IN_PROGRESS'), ('S123457', 'UNSUITABLE')]:
            result = self.run_command('record', sev, '--status', status, '--reason', 'test')
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.load('analyzed.json')['analyzed_sevs'], ['S123456', 'S123457'])
        self.assertEqual(len(self.load('outcomes.json')['cases']), 2)

    def test_retryable_failure_is_retained_without_permanent_exclusion(self):
        self.assertEqual(self.save(['S123456']).returncode, 0)
        self.assertEqual(self.run_command('record', 'S123456', '--status', 'RETRYABLE', '--reason', 'timeout').returncode, 0)
        self.assertEqual(self.load('analyzed.json')['analyzed_sevs'], [])
        self.assertEqual(self.load('outcomes.json')['cases']['S123456']['status'], 'RETRYABLE')

    def test_new_discovery_does_not_erase_outcomes(self):
        self.assertEqual(self.run_command('record', 'S123456', '--status', 'USED', '--reason', 'task exists').returncode, 0)
        self.assertEqual(self.save(['S123457']).returncode, 0)
        self.assertEqual(self.load('analyzed.json')['analyzed_sevs'], ['S123456'])

    def test_imported_analyzed_history_survives_discovery(self):
        self.state.mkdir(mode=0o700)
        (self.state / 'analyzed.json').write_text('{"analyzed_sevs": ["S123456"]}')
        self.assertEqual(self.save(['S123457']).returncode, 0)
        self.assertEqual(self.load('analyzed.json')['analyzed_sevs'], ['S123456'])

    def test_empty_receipt_stays_an_explicit_empty_pool(self):
        self.assertEqual(self.save([]).returncode, 0)
        self.assertEqual(self.load('candidates.json')['sevs'], [])

    def test_failed_verification_remains_in_retry_pool_without_becoming_eligible(self):
        self.assertEqual(self.save(['S123456']).returncode, 0)
        receipt = self.root / 'retry.json'
        receipt.write_text(json.dumps({
            'schema': 'oaoa.sev-discovery.v1',
            'generated_at': '2026-11-11T20:00:00+00:00',
            'selected': [], 'complete': True,
            'verification_failure_count': 1,
            'verification_failures': [{'sev': 'S123456', 'error': 'timeout'}],
        }))
        result = self.run_command('save-discovery', '--receipt', str(receipt))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.load('candidates.json')['sevs'], ['S123456'])
        self.assertEqual(self.load('candidates.json')['eligible_sevs'], [])
        self.assertEqual(self.load('candidates.json')['retryable_sevs'], ['S123456'])

    def test_invalid_receipt_does_not_replace_last_good_pool(self):
        self.assertEqual(self.save(['S123456']).returncode, 0)
        result = self.save(['logview:context:mid'])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.load('candidates.json')['sevs'], ['S123456'])

    def test_global_identity_error_does_not_erase_prior_pool(self):
        self.assertEqual(self.save(['S123456']).returncode, 0)
        receipt = self.root / 'blocked.json'
        receipt.write_text(json.dumps({
            'schema': 'oaoa.sev-discovery.v1',
            'generated_at': '2026-11-12T20:00:00+00:00',
            'selected': [], 'verification_failure_count': 0,
            'verification_error': {'error': 'agent_role_denied', 'failure_scope': 'caller_identity'},
        }))
        result = self.run_command('save-discovery', '--receipt', str(receipt))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.load('candidates.json')['sevs'], ['S123456'])
        self.assertEqual(self.run_command('check-access').returncode, 3)

    def test_unscreened_private_acquisition_is_pending_not_eligible(self):
        receipt = self.root / 'private.json'
        receipt.write_text(json.dumps({
            'schema': 'oaoa.sev-discovery.v1',
            'generated_at': '2026-11-12T20:00:00+00:00',
            'selected': [{'sev': 'S123456', 'generated_revision_count': 1}],
            'verification_failure_count': 0,
            'risk_screening': {'status': 'not_performed'},
        }))
        result = self.run_command('save-discovery', '--receipt', str(receipt))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.load('candidates.json')['eligible_sevs'], [])
        self.assertEqual(self.load('candidates.json')['pending_eligibility_sevs'], ['S123456'])
        self.assertEqual(self.load('candidates.json')['sevs'], ['S123456'])

    def test_known_access_denial_blocks_automatic_discovery(self):
        self.state.mkdir(mode=0o700)
        (self.state / 'selection_status.json').write_text(json.dumps({
            'status': 'BLOCKED_SOURCE_ACCESS', 'reason': 'agent_role_denied',
        }))
        result = self.run_command('check-access')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'BLOCKED_SOURCE_ACCESS')

    def test_parallel_updates_do_not_lose_outcomes(self):
        commands = [[sys.executable, str(SCRIPT), '--state-dir', str(self.state), 'record', sev,
                     '--status', 'USED', '--reason', 'test'] for sev in ['S123456', 'S123457']]
        processes = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for cmd in commands]
        for process in processes:
            _, err = process.communicate()
            self.assertEqual(process.returncode, 0, err)
        self.assertEqual(self.load('analyzed.json')['analyzed_sevs'], ['S123456', 'S123457'])


if __name__ == '__main__':
    unittest.main()
