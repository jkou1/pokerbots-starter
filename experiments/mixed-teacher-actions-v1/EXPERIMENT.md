# Mixed Professor Pete + Chatty Carlos action imitation (CPU preparation)

Problem: narrow single-teacher supervision can leave postflop passivity and strategic coverage gaps. Earlier models showed zero teacher-bet recall; the first repaired base checkpoint recovered some betting but preflop retention remains imperfect.

Hypothesis: one balanced mixture of actual Pete and Carlos decisions, each paired only with that teacher's own decision-time state, teaches broader betting/sizing behavior than another narrow single-teacher update.

Targeted change: discover canonical teacher IDs from raw seat maps, collect each teacher's own public matches with a frozen cutoff, replay all hands through the authoritative engine, and retain only legal flag-clean teacher action+amount targets across all streets. No winner-only selection. Preserve per-teacher observed street/action frequencies when balancing teachers equally using unique examples. Teacher labels remain in provenance/tags, never added to the student prompt. Public current-hand chatter may be represented as unverified context; optional outgoing say is not a target. No private scratchpads/reasoning are invented and no cleanup targets are reconstructed.

Source controls: match/deal groups are split before mixing across both teachers. A match containing both teachers belongs to one split. Preserve exact raw bytes, actual RawJSON URLs, hashes, listing coverage/cutoff, failures and duplicate-source receipts. Student inputs exclude opponents' hidden cards, future actions/board/outcomes and current-action stack_after.

Test: complete engine replay and requested-target legality; no teacher fallback/error/truncation targets; cross-teacher match/deal split intersection empty; remote upload membership/sample checks; actual managed prompt/target boundary. Fixed mixed-teacher selection stratified by teacher/street/action, existing147postflop and354preflop retention diagnostics, legal enum/amount tests, then paired official poker games. Final holdout never chooses checkpoints. Before promotion inspect table talk for workplace appropriateness within five minutes.

Success: improved official poker placement/chips with legal rate>=99%, meaningful postflop betting recovery, preserved checking/preflop behavior, and no cleanup/reliability regression. Teacher agreement and training loss are diagnostics, not poker quality.

Stop/extension policy: one initial pilot capped at10updates with checkpoints5/10; no blind40-update budget. Automatic decision rules require current fixed-selection evidence, action-only class-balanced/bet CE, reliability and retention checks. Do not extend merely because budget remains. Missing validation at the cap means release GPUs and wait for evidence. Any extension is a separately recorded coordinator decision with a selected parent checkpoint. No GPU launch currently authorized.

Budget proposal pending corpus counts: one4GPU SFT replica,0rollout/0eval replicas; batch64 or128 chosen explicitly for useful label coverage, modest LR from a behavior-validated parent. Starting from the currently stronger reliable SFT checkpoint can avoid relearning protocol; use base only if retention/official poker evidence rejects that parent. Root coordinates allocation with primary GRPO.

## Approved initial pilot before submission

Root approved one queued BASE pilot:4GPUs,10updates,batch128,LR5e-6,checkpoints atoptimizeriterations4/9,0rollout/eval engines. The account rejects custom priority fields; use its default scheduler queue and never stop an active GRPO job for this pilot. Initial1280source examples contain exactly640Pete and640Carlos after deterministic seed42 shuffle. Actual first managed batches must be checked by task-ID provenance. Stop naturally at10; no extension without fixed balanced256 selection, legality/retention, action-only CE and official poker evidence. Detailed numeric gates are frozen inSTOP_AND_EXTENSION_POLICY.json.
