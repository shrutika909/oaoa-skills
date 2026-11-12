#!/usr/bin/env python3
"""Keep private SEV discovery and outcome files for evidence-pack selection."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


STATUSES = ('IN_PROGRESS', 'USED', 'UNSUITABLE', 'REJECTED', 'RETRYABLE')


def canonical_sev(value):
    text = str(value).strip().upper()
    if not re.fullmatch(r'S?[1-9][0-9]{3,}', text):
        raise ValueError('expected a canonical SEV number')
    return 'S' + text.removeprefix('S')


def write_json(path, value):
    fd, temp = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    save = commands.add_parser('save-discovery')
    save.add_argument('--receipt', required=True)
    record = commands.add_parser('record')
    record.add_argument('sev')
    record.add_argument('--status', choices=STATUSES, required=True)
    record.add_argument('--reason', required=True)
    record.add_argument('--evidence', help='Private path to the outcome receipt')
    args = parser.parse_args()
    os.umask(0o077)

    # Validate inputs before replacing the last successful discovery.
    if args.command == 'save-discovery':
        raw = Path(args.receipt).read_bytes()
        receipt = json.loads(raw)
        if receipt.get('schema') != 'oaoa.sev-discovery.v1' or not isinstance(receipt.get('selected'), list):
            raise ValueError('expected an evidence-pack discovery receipt')
        generated_at = receipt['generated_at']
        if datetime.fromisoformat(generated_at).tzinfo is None:
            raise ValueError('discovery timestamp requires a timezone')
        sevs = sorted({canonical_sev(row['sev']) for row in receipt['selected']})
        failures = receipt.get('verification_failures', [])
        if receipt.get('verification_failure_count', 0) != len(failures):
            raise ValueError('verification failures require per-source retry receipts')
        retryable_sevs = sorted({canonical_sev(row['sev']) for row in failures})
        candidates = {
            'source_kind': 'sev', 'sevs': sorted(set(sevs + retryable_sevs)),
            'eligible_sevs': sevs, 'retryable_sevs': retryable_sevs,
            'discovery_generated_at': generated_at,
            'discovery_complete': receipt.get('complete'),
            'verification_failure_count': receipt.get('verification_failure_count'),
            'discovery_receipt_sha256': hashlib.sha256(raw).hexdigest(),
        }
    else:
        sev = canonical_sev(args.sev)

    state = Path(args.state_dir).expanduser().resolve()
    if any((parent / marker).exists() for parent in (state, *state.parents)
           for marker in ('.git', '.hg', '.sl')):
        raise ValueError('selection state must be outside repositories')
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    if state.stat().st_mode & 0o077:
        raise ValueError('selection directory must have private permissions')
    with (state / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        outcomes_path = state / 'outcomes.json'
        outcomes = json.loads(outcomes_path.read_text()) if outcomes_path.exists() else {'source_kind': 'sev', 'cases': {}}
        analyzed_path = state / 'analyzed.json'
        analyzed = json.loads(analyzed_path.read_text()) if analyzed_path.exists() else {'analyzed_sevs': []}
        skipped = {canonical_sev(value) for value in analyzed['analyzed_sevs']}
        if args.command == 'save-discovery':
            write_json(state / 'discovery_receipt.json', receipt)
            write_json(state / 'candidates.json', candidates)
        else:
            previous = outcomes['cases'].get(sev, {})
            row = {
                'status': args.status, 'reason': args.reason,
                'evidence': args.evidence,
                'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            }
            row['history'] = previous.get('history', []) + ([{k: v for k, v in previous.items() if k != 'history'}] if previous else [])
            outcomes['cases'][sev] = row
        write_json(outcomes_path, outcomes)
        skipped.update(sev for sev, row in outcomes['cases'].items() if row['status'] != 'RETRYABLE')
        skipped.difference_update(sev for sev, row in outcomes['cases'].items() if row['status'] == 'RETRYABLE')
        write_json(analyzed_path, {
            'analyzed_sevs': sorted(skipped),
        })
    print(json.dumps({'state_dir': str(state), 'command': args.command}))


if __name__ == '__main__':
    main()
