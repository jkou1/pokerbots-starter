# Genuine concise cleanup retention (CPU preparation only; no training authorized)

Problem: full-game incumbent/frozen cleanup repeatedly exceeds5000characters, causing retries and cuts that dominate latency. Short output alone is insufficient:2/6 fresh short replies contained wrong board/stacks.

Hypothesis: retaining genuine concise and factually correct cleanup replies can reduce retries/token cost without damaging betting or useful memory.

Targeted change: use only actual successful own-model cleanup targets from fresh TRAIN seeds, unchanged. Preserve original runtime input/output and hashes. To supervise only the nominated reply, retain original system/user observations and serialize prior own assistant/tool items as explicit recorded-history user context. This is a changed input representation, not an exact original conversation; label it accurately. No private reasoning or scratchpad is fabricated, no public-history missing memory reconstructed. No SELECT stress input enters training.

Test: source hash/provenance/seed split checks, actual cleanup-success and exact final-board/stacks/action-fact validation. Evaluate on heldout real overlong cleanup inputs and full official games: character limit compliance, factual retention, retry/cut counts, total tokens/latency, and downstream betting/placement. Pair against parent; preserve postflop bet/check recall and legal action enum.

Success: fewer overlong updates/retries/cuts, correct notes, lower full-game cost, preserved poker quality and legal actions. Do not optimize shortness alone.

Stop: any fabricated target, source/selection leakage, factually wrong board/stacks, malformed cleanup tool, material betting or placement regression.

Budget: not launched or uploaded. Four unique validated short targets only; preservation weight must be judged by target tokens as well as example count. Long cleanup targets can dominate action loss; cap intended cleanup contribution at a modest fraction, never blindly use10–15%examples. No further GPU training without coordinator allocation.
