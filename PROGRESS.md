# Overnight poker experiments

Coordinator: Codex. Window: Sunday 2026-11-15 00:27–09:00 PST.
Standing orders: `/Users/lance/Documents/pokerbots-starter-grpo-history/AGENTS.md`.

## Operating policy

- Maximize leaderboard placement while preserving working entries and dependencies.
- Use the reserved 10-GPU allocation for useful training and evaluation; actively triage stalls, errors, and slow throughput.
- Avoid direct paid APIs. Use existing AC2 allocation; Codex OAuth or Kimi CLI for additional reasoning, preferring highspeed models.
- Isolate experiments and record dataset/checkpoint/configuration lineage. Preserve final holdouts.
- Autonomous promotion is authorized after functional validation and a workplace-appropriate table-talk review taking at most five minutes per promotion. Repair failed promotions and preserve rollback options.
- Existing caffeinate and network availability are supplied by user.

## Current status — 00:29 PST

- Main branch worktree created at `/Users/lance/Documents/pokerbots-main`, fast-forwarded to `origin/main` (`f9022ff`); this file lives in its root.
- GRPO `train_dddb9d4abf5d` is running: historical 20k stack tasks, frozen self-play from `ckpt_ad74c826c9ad`, requested 100 steps / 16 rollouts. Existing launch agent verified four frozen-opponent test hands with zero errors.
- Deployments: `combined-sft-v3` and `selfplay-ad74c826c9ad`, each one GPU; custom harness relay uses zero GPUs.
- PokerBench agent reports background chunked upload of 80k train / 20k test / preflop datasets. Membership and protocol compatibility need verification before training.
- Existing GEPA attack evidence is preliminary (tiny validation sets and endpoint failures); no promotion justified yet.

## Assignments

- `rl_ops`: GRPO queue/runtime health, reward signal, rollout throughput and checkpoint readiness; repair failures.
- `sft_data`: audit PokerBench conversion/upload and prepare short, protocol-correct SFT experiment; coordinate GPU allocation before launch.
- `eval_promote`: identify incumbent and checkpoint mappings, evaluate existing strong candidates without changing the live RL connector.
- Coordinator: GPU scheduling, highest-ROI next experiments, promotion decisions, durable status and monitoring.

## Next decisions

1. Confirm actual GRPO GPU allocation and healthy completed graded rollouts.
2. Verify current arena entry and existing candidate reliability before allocating more serving GPUs.
3. Run the smallest useful PokerBench SFT pilot as soon as capacity permits; avoid full 80k training before proving target format and live poker behavior.
4. Keep training, selection, and final evaluation separate; prioritize valid actions and official-game placement over training loss or imitation accuracy.

## Update — 00:30 PST

- GRPO main job reserves 6 GPUs. Its configured in-run evaluation sidecar requires another 2; two serving deployments bring peak demand to the full 10-GPU allocation. Additional SFT must be scheduled after RL or an evidence-based reallocation.
- Incumbent confirmed: `return of rain man`, serving `combined-sft-v3`, checkpoint `ckpt_51eee61470f7`, iteration 39 of `train_87b51a9211a1`. Direct paired-game evaluation preparation is active; platform evaluations will also be used where efficient.
- PokerBench upload resolved to dataset `pokerbench-unified-20k`, 19,992 unique tasks. Existing targets omit the known necessary nonempty reasoning boundary, and conversion rounds fractional amounts. These datasets will not be trained unchanged. A corrected, versioned dataset with grouped deduplication/splits and exact amount representation is being prepared.
- Durable read-only observer started (`/tmp/pokerbots-coordinator-watch.py`, PID 83159), polling AC2 jobs/deployments/training every 60 seconds until 09:00 PST. Snapshot: `overnight-status.json`; log: `/tmp/pokerbots-coordinator-watch.log`. Coordinator and RL agent handle triage; observer itself does not stop jobs.

## Objective clarification — 00:31 PST

The user explicitly targets **#1 on the leaderboard and defending the lead through day 2**. Current autonomous execution window remains through Sunday 09:00 PST. Favor broad, high-impact improvements and reliable promotion over minor metric tuning. Prepare durable monitoring/continuation for day 2.

- Frozen `ad74` is iteration 19 of the same combined SFT training run as incumbent iteration 39; paired comparison tests early versus late SFT, not independent step2 training.
- Existing GEPA agent has been assigned a bounded fresh paired attack-versus-control validation on external `ac-vals-model` (15-minute initial budget, max four concurrent calls), with no new GPUs or paid provider APIs. Further search/training depends on actual incremental effect.
- Current incumbent recent arena audit: 471 decisions across ten matches, zero fallbacks/format errors, no table talk.

## Required experiment framework — 00:32 PST

Every experiment records **problem → hypothesis → targeted intervention → controlled test → success/stop criteria** before launch. Inherited jobs are explicitly labeled as retrospective framing. Agents have been instructed to use this framework for every experiment.

| Experiment | Problem / hypothesis | Targeted intervention | Test and decision rule |
| --- | --- | --- | --- |
| Historical-stack GRPO (inherited; framing retrospective) | Policy may generalize poorly to unequal tournament stacks; rewarded play against a fixed strong parent may improve adaptation | Train ad74 on historical stack profiles with fixed ad74 opponents, preserving live reward/prompt/config | Verify graded live rollouts, nondegenerate within-group reward, update throughput; compare selection checkpoints to parent and gate promotion on official games. Triage infrastructure failures immediately; stop/reallocate on sustained broken signal or poor projected ROI |
| Existing checkpoint comparison (already launched; framing retrospective) | More SFT updates need not improve real poker; iteration19 may outperform iteration39 | Same official30hand deals/seats/opponents for ad74 versus incumbent |12 paired games initially plus AC2 smoke; inspect placement, chip EV, action failures, latency. Escalate sample only if promotion-relevant; do not promote on imitation loss |
| PokerBench SFT (preparation only) | Incumbent has only19 unique postflop replay targets; broader labeled postflop coverage may improve decisions | Correct protocol boundary, exact chip scaling, scenario-group dedup/splits; short incumbent continuation rather than immediate full dataset training | Verify semantic/legal targets and managed SFT serialization; checkpoint20/40; compare official games vs parent. Stop on protocol failures, reliability regression, or poor poker selection results |
| Pete postflop SFT (candidate) | Leader Pete outperforms us while unused public postflop demonstrations exist; targeted imitation may improve value extraction | Export legal decision-time postflop targets under existing source-match splits; short continuation with clean replay | Source replay/provenance audit, protocol smoke, matched official-game parent comparison. Prefer over PokerBench if it provides verified useful data faster; never imitate lucky outcomes by winner-only filtering |
| Table-talk validation (predeclared) | Tiny prior optimized validation may reflect selection/noise rather than attack effect | Existing best messages versus neutral/silent controls, no new search | Paired identical decision states, official unhinted prompts, legal action checks, external ac-vals-model; initial15min budget. Stop absent meaningful incremental effect; no training/promotion from raw attack hit rate alone |

Leaderboard snapshot: overall leader Professor Pete rating1329, EV+64.2BB/100, zero fallbacks; leading team Accord v2 rating1163, EV+30.1BB/100. Our aggregate rating1024/EV+15.4 includes older entries. Recent incumbent reliability is good, so the leading improvement hypothesis is postflop strategy rather than additional format-only training. A tiny current style sample suggests low postflop betting; treat this as a hypothesis, not a proven defect.

## Throughput adjustment — 00:34 PST

AC2 incumbent smoke has two of four hands complete with no format errors, but roughly156–177seconds per hand against external `ac-vals-model`. The incumbent policy itself is fast (~0.8seconds/action); external opponents dominate latency. Keep the already-running bounded official comparisons, and add a fast paired screen against the existing frozen ad74 endpoint, sharing its capacity with RL. Hypothesis: local frozen opponents permit much faster rejection of bad checkpoints without extra GPUs; confirm measured throughput before scaling concurrency. Fast screening is not a substitute for varied-opponent/full-game promotion evidence.

Fresh Pete postflop collection/export, corrected PokerBench upload, live RL monitoring, paired candidate evaluations, independent PokerBench amount-semantic audit, and bounded talk validation are assigned concurrently. GPU scheduling remains centralized to avoid oversubscription.

## Ready pipeline — 00:34 PST

- Fresh Pete source collection:109complete matches, zero download failures, zero engine-replay quarantines. Postflop targets:1,250train /147selection /103final; preflop preservation targets:2,537train /354selection /245final. Decision-time observations exclude hidden/future information; private reasoning is not fabricated. Postflop action targets contain no table talk.
- Authorized next queued experiment: continue incumbent `ckpt_51eee61470f7`,75%fresh Pete postflop /25%preflop preservation,40updates,batch64,learning rate2e-6,checkpoint20. Rationale: target broad postflop behavior while preserving preflop; defer the greater PokerBench domain shift until this lower-risk source is tested. Four GPUs; no inference/eval replicas during SFT. Actual submission receipt pending.
- RL sampler became ready00:33:29, trainer startup00:33:23. Startup took several minutes; no current evidence of a harness failure. Exact inherited CLI omitted explicit checkpoint interval and learning rate; do not assume checkpoint10 exists. It requests in-run selection every20steps.
- Fast AC2 paired32single-hand selection is launched versus existing frozen ad74: incumbent `eval_521f73148d31`, parent `eval_7353b52d4873`, two concurrent hands each. No new serving GPUs. Slow full-game comparisons remain in parallel.

## Live signal and queued pilot — 00:36 PST

- GRPO has real graded live rollouts. First observed group has fifteen rewards5.0 and one6.5, zero format failures; second group also shows variation. Monitor complete task groups rather than confusing cross-task reward variation with GRPO advantage signal. Companion observer `/tmp/pokerbots-rl-signal.py` saves `/tmp/pokerbots-rl-signal.json` every60seconds.
- Preferred Pete postflop continuation submitted: **`train_e3fba0323bd2`**, pending resources. Verified dataset1667unique training examples (1250postflop+417preflop), postflop selection147, final103. Receipt/config under `/Users/lance/Documents/pokerbots-pokerbench/experiments/pete-postflop-v1/`. Uses four catalog-default training GPUs, one training replica, zero rollout replicas, evaluation off; unsupported explicit GPU/eval-replica fields were rejected before successful submission. No duplicate training job was created.
- A same-data base-start control is prepared but not submitted; it can run alongside continuation if RL capacity is reallocated, providing a targeted parent-choice comparison while saturating8training+2serving GPUs.
- AC2 incumbent smoke completed4/4: three clean hands, one enum-invalid `submit_action({"action":"submit"})`. This is a model behavior failure, not auth/truncation. Preserve the official parser and add held-out enum/cleanup reliability checks for new checkpoints. Recent arena0/471failure evidence remains distinct from this smoke failure.

## Priority pivot — 00:38 PST

**Problem confirmed:** On147held-out Pete postflop decisions, both incumbent and ad74 made zero of39teacher bets; all39became checks. They also matched all77teacher checks and were100%legal. Incumbent action distribution:116checks,17folds,11calls,3raises, zero bets. This is a focused postflop passive-collapse signal, not merely weak overall imitation accuracy.

**Hypothesis:** Narrow previous SFT postflop coverage suppressed betting; broad legal leader postflop supervision can restore value betting quickly without sacrificing tool reliability or sensible checks.

**Targeted decision:** Gracefully stop inherited broad GRPO and its queued evaluation sidecar, preserve parent/checkpoints/rollout evidence, and use released8GPUs for two parallel4GPU Pete pilots: incumbent continuation (LR2e-6) and independent base start (LR5e-6), same1667examples/40updates/checkpoint20. Two existing serving deployments retain2GPUs, totaling10. This avoids waiting for a long broad RL run before addressing a directly measured defect. Teardown/start verification is assigned to RL/data agents.

**Predeclared diagnostic:** Restore at least10/39teacher bets while retaining at least69/77teacher checks and99%legal outputs. Also inspect bet sizes/street breakdown, preflop preservation, known enum regression, and cleanup. These diagnostics select candidates; promotion additionally requires matched official-game evidence, separate final holdout, work-safe table-talk review, and rollback readiness. No ad74 promotion based solely on its slightly higher overall imitation agreement.

## Resource transition verified — 00:39 PST

- GRPO and its evaluation sidecar are stopped; parent/ad74 and incumbent deployments are preserved. Final captured RL signal:217scored samples,12complete groups,10nondegenerate,3model-format failures; no saved checkpoint or verified optimizer update. The run was not zero-signal or broken; it was stopped for higher expected ROI from fixing measured postflop collapse.
- Both targeted SFT pilots are **running**: continuation `train_e3fba0323bd2` / `job_f528c97a9589`, base control `train_4cc69b58d8e9` / `job_b8b470832d80`. Each reserves4GPUs; two serving deployments reserve2: **10/10allocated**. Confirm training throughput/utilization after startup; allocation alone is not saturation.
- Fast incumbent AC2 selection completed32hands with zeroformaterrors, meanEV+0.344BB/hand. Parent comparison interim is noisy; no evidence to replace incumbent with ad74.
- Root verified authenticated Safari AC2arena controls and currententry `return of rain man` / `infer_b0f5e9429b7e`. Arena promotion/rollback access is ready; no entry was changed.
- Practical promotion gate and rollback criteria are recorded in `/Users/lance/Documents/pokerbots-overnight-eval/experiments/overnight-evaluation.md`.

## Lineage verification and bounded alternatives — 00:42 PST

- Requested continuation configuration correctly resolves to `from_checkpoint=ckpt_51eee61470f7`, but AC2effective GETconfiguration omits the field. Native CLI uses the same SDK/v2submission route, so switching CLI alone is not an independent fix. Historical warm-started GRPO and OPSD also omit it fromeffective metadata; prior GRPO emitted the trained protocolmarker in387/389policyactions, supporting that metadata omission alone does not prove lost weights. Runtime continuation proof remains pending; compare initial same-batch losses/restorelogs before causal parent-choice claims.
- Midhand-reset RL would require1–2hours of implementation/parity/leakage tests. Deferred as poor immediate ROI; existing frozen-preflop/staged-postflop training is a lower-engineering alternative if later RL is justified.
- Independent PokerBench audit confirms labels are street totals and the corrected2xchip-scaling exporter is appropriate. Corrected versioned PokerBench datasets are uploaded/verified and ready as a fallback; raw rounded dataset is not a training candidate.
- A bounded25minute CPU/CLI preparation task is creating64diverse TRAIN-only synthetic Kimi teacher rationales with exact expert action targets. Problem: current weights emit only the6token protocolmarker rather than strategy reasoning. Hypothesis: concise genuine synthetic teacher explanations may retain strategy computation better than marker-only action classification. Rationales must be explicitly labeled synthetic, use only decision-time information, avoid unsupported equity claims, and never masquerade as Pete private reasoning. No GPUexperiment is authorized until a remaining defect justifies it.

## First-update verification — 00:46 PST

- Warmstart is strongly supported by matching-batch initial losses: continuation0.0321547/gradientnorm1.6268 versus base1.0245289/gradientnorm85.0305, with matching input batches/seed. Combined with staged runtime paths, this resolves the practical lineage concern; APIeffective metadata omission is not evidence of lost weights.
- Managed boundary audit failure was stale: `student_prompt` already ends in `<think>\n`, and target begins `Tool call follows.\n</think>` with supervised closing token before real toolcall. Local audit is being corrected to validate combined prompt+target. No targetformat failure observed.
- Training steps are advancing (~15–30seconds/update after startup); first20update checkpoints expected within minutes, not hours.
- Isolated branch `/Users/lance/Documents/pokerbots-cleanup-rl`, `training-skip-final-cleanup`, implements boolean opt-in skip-final-cleanup only for exactly1hand. Default behavior/official30hand games remain unchanged.28focusedtests passed,1skipped; mocked same-seed action/stack/grade parity verified with cleanupcalls6→0. Live timing validation and a safe harness-switch plan are pending; no connector changed.
- Future local official-game collectors now save perhand progress and bounded timeoutfailure receipts; already-running collectors are not restarted. Gateway telemetry confirms they are advancing.

## Next pipeline slot — 00:48 PST

- Both Pete pilots are advancing at roughly10seconds/update after warmup (steps15/16), with first20update checkpoints imminent and final40updates projected around00:52. Conversion requests are owned by the data agent to avoid duplicates.
- Canonical managed-SFT boundary fix cherry-picked onto main as `3230221`;7focused tests passed in its isolated worktree. It checks combined prompt+target and rejects double-newline/missing or unsupervised closing-tag errors.
- Authorized next queued4GPU experiment: corrected PokerBench base-start pilot,40updates,batch64,LR5e-6,checkpoint20, zero rollout/eval engines. **Problem:** Pete-only demonstrations may leave strategic coverage gaps. **Hypothesis:** broader solver-derived labels, with verified chip scaling/group splits/protocol, improve decision quality. **Target:** corrected versioned PokerBench only. **Test:** stratified selection diagnostics and matched official poker versus incumbents/Pete candidates; legal>=99%, sizing checks, separate final holdout; never select on training loss alone. Source-quality audit is a launch prerequisite.
- Resource plan after current pilots:4GPU nexttraining+2preservedserving+2newPete candidate deployments=8; remaining2GPUs can run a checkpoint-native AC2evaluation of final versus early weights. Every allocation must wait for verified released capacity.

## User steering: GRPO remains the main track — 00:53 PST

The user emphasized that GRPO is the recommended method and setup failures must be diagnosed rather than interpreted as failure of the approach. Coordinator acknowledged the previous stop was premature before a verified optimizer update/checkpoint. The run had real signal; its stop was an ROI scheduling choice, not evidence against GRPO.

**Updated plan:** Finish the two short running SFT pilots, then restore GRPO immediately. Keep the existing ad74 checkpoint/historical dataset/opponents/reward/prompt lineage, make checkpoint cadence explicit, verify real optimizer updates/checkpoints, and monitor infrastructure/model-format failures separately. Use6GPUs with in-run evaluation off and manual checkpoint comparisons, leaving4serving GPUs for incumbent, frozen parent, and two SFT/RL candidate slots:10total. The exact launch/monitor recipe is owned by RLoperations.

**Canceled GPU authorizations:** PokerBench pilot launch is on hold; its corrected v3 preparation/upload remains CPU-only. The proposed extra2GPU standalone checkpoint evaluation is canceled; no such job launched. Candidate evaluation will use the two1GPU slots sequentially after verified capacity release.

The Pete SFT experiment remains a targeted parallel test of measured0/39bet recall; its result can inform a later GRPO initialization, but does not replace reward-based training. A properly graded live hand, an optimizer update, and a saved checkpoint are required before claiming RL progress.
