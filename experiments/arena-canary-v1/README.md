# Actual Arena canary: inactive until promotion confirmation

The poller is read-only. It never makes model calls, promotes, submits, cancels, or rolls back. Root must confirm the actual Arena entry and atomically set activation.json with active=true, promotion_confirmed=true, the confirmed model alias, immutable inference_id, version, and UTC cutover_utc. The example file documents the fields; it is deliberately inactive. No credential belongs in activation.json.

Poll interval45seconds, bounded30–60, deadline2026-11-15T17:00Z. Verified query: native analytics spans, inference.request, immutable inferenceID filter; retain only attrs.conversation_id matching vals-arena/m_.../hand-N/seatN. Use complete/error-ended spans, actual runtime-list input/output, and the last visible user observation. Optional Arena tool definitions are unavailable; p_win/read requirements are unsupported rather than inferred from outputs.

Status: /tmp/pokerbots-arena-canary-status.json. Atomic alerts: /tmp/pokerbots-arena-canary-alerts.json. Log: /tmp/pokerbots-arena-canary.log. Private exact evidence and dedup state remain owner-only in ignored evidence/. Git and dashboard artifacts contain no raw private traces.

Unique span attempts are deduplicated by span_id. Logical decisions are grouped by conversation plus visible-observation SHA256, and cleanup by conversation. A failed attempt conservatively marks that unique turn invalid; attempted spans and logical denominators are reported separately. Version and cutover pins prevent baseline/candidate mixing. First40 unique decisions trigger a guard at>=5%invalid; endpoint/unparseable/truncated/no-tool outputs or workplace talk flags alert immediately. Repeated enum and cleanup failures alert. Root decides action. Poker losses alone are not protocol failures.

Legal fold/check/call and bet/raise street-total intervals are read from that decision's own Legal actions line. Cleanup requires exactly one update_scratchpad, contents-only string<=5000characters, no truncation or wrong tool. This establishes protocol shape, not memory factuality. Own say uses a limited lexical workplace flagger; flags need human/coordinator review and absence of flags is not full moderation certification.

Run validate.py for offline fixture tests. It uses only recorded Arena incumbent and selection/native failure fixtures, not model calls or training targets. validation.json records hashes and aggregate results. Actual backend monitoring remains separate from this parser validation.
