from vals_tools.cleanup_score import cleanup_protocol


def test_accepted_duplicate_updates_do_not_pass_exact_protocol():
    attempt = {'update_calls': ['{"contents":"one"}', '{"contents":"two"}'],
               'ignored_calls': 1, 'outcome': 'ok'}
    result = cleanup_protocol([{'result': 'updated', 'attempts': [attempt]}])
    assert result['accepted_updated'] == 1
    assert result['exact_valid_final_updates'] == 0
    assert result['multiple_update_attempts'] == 1
    assert result['wrong_tool_calls'] == 0


def test_accepted_update_with_extra_wrong_tool_is_reported():
    attempt = {'update_calls': ['{"contents":"notes"}'],
               'ignored_calls': 1, 'outcome': 'ok'}
    result = cleanup_protocol([{'result': 'updated', 'attempts': [attempt]}])
    assert result['accepted_updated'] == 1
    assert result['exact_valid_final_updates'] == 0
    assert result['wrong_tool_calls'] == 1


def test_retry_and_cut_do_not_claim_accepted_memory():
    attempt = {'update_calls': ['{"contents":"' + 'x' * 5001 + '"}'],
               'ignored_calls': 0, 'outcome': 'too_long'}
    result = cleanup_protocol([{'result': 'cut', 'attempts': [attempt, attempt]}])
    assert result['retried_turns'] == 1
    assert result['cut'] == 1
    assert result['accepted_updated'] == 0
    assert result['exact_valid_update_attempts'] == 0
