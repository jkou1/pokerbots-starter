# Exact V2 RL20 ablation stopped

Twenty authorized calls completed, with full HTTP request/response bodies preserved securely and all finish reasons `tool_calls`. No retries or additional policy calls were made. Cumulative V1/V2/ablation usage is60calls.

Eight hinted notes exceeded the frozen1500-character acceptance cap: cases1/2/3/4/5/6/8/10 were5328/5722/2255/3921/1627/1544/3364/5231characters. Thus strict useful acceptance is at most2/10, below the required8/10, irrespective of remaining semantic review. All ten unhinted notes exceeded1500characters. The conservative full-claims parser accepted zero in each arm; length failures independently establish the stop decision.

No training, promotion or further variants. This does not evaluate native offline OPSD optimization, which was never launched.

Treatment plumbing was checked read-only from actual captured request bodies: the teacher hint was appended exactly once to `messages[0].content`, the request had no competing `input` field, and system hashes differed across arms. Official HF CPU rendering of the actual wire messages/tools retained the hint inside the system turn in all ten cases, with hashes and token ranges in `wire-hint-audit.json`. This demonstrates local wire/render treatment; actual backend model-input tokens/attention are not exposed. Independent server-parser review remains necessary before interpreting the failure as model inability rather than unsupported treatment plumbing.

Correction to previous CPU token-length audits: canonical flat tool definitions were used there, whereas the actual HTTP body uses OpenAI function-wrapped definitions. The wire audit renders the actual definitions and explicitly parses historical argument JSON strings as required by the HF template. No prompt treatment or actual request was changed during this read-only audit.

Exact private original contexts, replies, HTTP bodies and rendered prompts remain ignored local evidence. Aggregate result, completion and wire-treatment audits contain no raw scratchpads.
