# V2 model-only RL20 ablation

Problem: OWN10 did not obey the closed-world memory hint. Hypothesis: the stronger RL20 policy follows that same hint while preserving useful visible current/prior facts.

The ten original TRAIN contexts, teacher hints and published canonical tools are unchanged from V2; their JSONL bytes and SHA256 are identical. Only the model changes to RL20 checkpoint11e7, immutable inference d9/version1. Temperature0, reply budget10000per arm, concurrency2 and intention-to-treat accounting remain unchanged. No source/hint edits after outputs. Twenty new calls bring cumulative probe use to60of64.

The frozen gate remains at least8/10strict useful hinted replies and at least3more than unhinted: one contents-only real cleanup call, <=1500characters, current+provided verified prior facts, and zero unsupported claims. Teacher hint target remains700characters. No training or promotion is authorized. Failure ends this memory avenue without further variants.

Complete request and response bodies are securely captured without authentication headers. Exact private source contexts and replies remain ignored local evidence. Canonical published tool definitions are supplied; original Arena offered tools are unavailable in telemetry. This is a model ablation, not OPSD training.
