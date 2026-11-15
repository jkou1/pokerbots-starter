"""Audit recorded cleanup acceptance and exact tool protocol without rewriting memory."""
import json
from collections import Counter


def cleanup_protocol(cleanups):
    attempts = [a for c in cleanups for a in c.get('attempts', [])]
    outcomes = Counter(a.get('outcome', 'unknown') for a in attempts)
    results = Counter(c.get('result', 'unknown') for c in cleanups)

    def counts(attempt):
        calls = attempt.get('update_calls', [])
        # The harness counts all non-first calls as ignored, including duplicate updates.
        wrong_tools = max(0, attempt.get('ignored_calls', 0) - max(0, len(calls) - 1))
        valid = False
        if len(calls) == 1:
            try:
                payload = json.loads(calls[0]) if isinstance(calls[0], str) else calls[0]
                contents = payload['contents']
                valid = isinstance(contents, str) and len(contents) <= 5000
            except (TypeError, ValueError, KeyError):
                pass
        strict = valid and wrong_tools == 0 and not attempt.get('truncated') and attempt.get('outcome') == 'ok'
        return bool(strict), wrong_tools

    audited = [counts(a) for a in attempts]
    return {
        'turns': len(cleanups),
        'attempts': len(attempts),
        'accepted_updated': results['updated'],
        'kept_unchanged': results['unchanged'],
        'cut': results['cut'],
        'retried_turns': sum(len(c.get('attempts', [])) > 1 for c in cleanups),
        'exact_valid_update_attempts': sum(valid for valid, _ in audited),
        'exact_valid_final_updates': sum(c.get('result') == 'updated' and bool(c.get('attempts')) and counts(c['attempts'][-1])[0] for c in cleanups),
        'wrong_tool_calls': sum(wrong for _, wrong in audited),
        'attempts_with_wrong_tools': sum(wrong > 0 for _, wrong in audited),
        'missing_update_attempts': sum(not a.get('update_calls') for a in attempts),
        'multiple_update_attempts': sum(len(a.get('update_calls', [])) > 1 for a in attempts),
        'attempt_outcomes': dict(outcomes),
        'result_counts': dict(results),
        'scope': 'Protocol/acceptance only; contents factuality is not established. Exact validity requires one update_scratchpad, string contents <=5000, zero other calls, no truncation, and harness outcome ok.',
    }


def aggregate_cleanup_protocol(rows):
    summaries = [row['cleanup_protocol'] for row in rows]
    numeric = {k: sum(s[k] for s in summaries) for k, v in summaries[0].items() if isinstance(v, int)} if summaries else {}
    for key in ['attempt_outcomes', 'result_counts']:
        counts = Counter()
        for summary in summaries:
            counts.update(summary[key])
        numeric[key] = dict(counts)
    numeric['scope'] = 'Recorded cleanup protocol/acceptance only, not factual-memory quality.'
    return numeric
