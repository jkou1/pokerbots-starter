# Overnight poker experiments

Coordinator: Codex. Window: Sunday 2026-11-15 00:27–09:00 PST.
Standing orders: `/Users/lance/Documents/pokerbots-starter-grpo-history/AGENTS.md`.

## Current status — 05:01 PST

- **Goal:** reach #1 and defend through day 2. Autonomous coordination continues until 09:00 PST. The latest cached public team page (02:47 PST) showed rank #16, rating 937; this is not a claim that the goal has been achieved.
- **Live entry:** `return of rain man`, inference `infer_b0f5e9429b7e`, checkpoint `ckpt_51eee61470f7`. Unchanged. The candidate is eligible for a monitored canary, but authenticated Arena control is unavailable (`cgWindowNotFound`). SDK/CLI/source inspection found no supported submission API. No guessed write or credential migration was attempted.
- **Selected candidate:** GRPO step 20, checkpoint `ckpt_11e7c430069c`, inference `infer_9efa1c614a32`, version 1. Selection was frozen before the separate final. Final six-game average place: **2.0 vs 3.17**; EV gain **75.37 BB/game**, 95% CI **[−23.21, +170.34]**. This is directional evidence, not proven superiority. Invalid actions: **2/298 vs 0/309**. Cleanup: **180/180 accepted vs 139/180**. Both exact error states passed four repeat probes each. Workplace review took 111 seconds; outputs were silent with `say` available. Factual memory accuracy remains imperfect.
- **GRPO end-to-end control:** own-account weights-only `ckpt_b5a8f86bbb45` eventually became serving-AVAILABLE at 04:55:52 PST, about 49 minutes after conversion request. A real-tool-ready one-GPU endpoint and fresh64 quality baseline are now launching as `infer_db04467416e4`; no longer RL is authorized until behavior is known. Raw save/serving conversion now work for the own family. Stronger old step-20 raw access remains blocked; original weights are safe.
- **Requested Pete/Carlos SFT:** completed all ten updates, exit code 0; both checkpoints are AVAILABLE. Both failed the frozen behavior gates. Final: 3/27 held-out bets, 37/43 checks, preflop agreement 76.55% vs 84.46%, strict cleanup 1/10. Actions remained legal. No extension, promotion or full-game expansion. Training and negative behavior audits are published in `coll_6c119f846b5e`. The failed teacher endpoint is retired; historical step 2 uses the candidate slot next.
- **GPU allocation:** four protected serving dependencies + four teacher-training GPUs = eight. Step 40 and step 90 failed the material advancement gate and are being retired after draining. The unused step 20 inference node may also be reclaimed after verified dependency checks; its checkpoint/results remain preserved. Planned next footprint: six GRPO GPUs + three protected serving endpoints (actual incumbent and two opponents) + one teacher-candidate endpoint = ten.
- **Account:** future AC2 writes use `lmathias@berkeley.edu`, UID 10464. Existing jobs retain their original owners; none are canceled merely to migrate identity.
- **Failure mining:** the public dashboard miner remains active every ten minutes until 09:00. It separates current-entry failures from older submissions, preserves source URLs/hashes, and labels coverage limits. Private scratchpads are not publicly observable.
- **Closed/on hold:** PokerBench training, table-talk search, and synthetic reasoning generation. The earlier 40-update SFT pilots are complete; action-token loss continued improving, so the prior convergence claim was corrected. Future extensions require held-out behavior evidence, not loss alone.

[AC2 evaluations](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals) include the completed final pair: [incumbent](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_be4a7c44dc07), [RL20](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_8a14524c0e64). Final evidence and freeze provenance are published in collection `coll_6dbffac3ae9c`; SFT action audits are in `coll_40d2b84e2fb5`. Static local diagnostics are labeled local rather than presented as native evaluations.

## Decision log

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

## Early-stop correction and GRPO restart — 00:57 PST

The user correctly challenged why the base SFT pilot ran its entire40update budget without an early-stop decision. Coordinator acknowledged a monitoring gap: job health was watched, but the20update checkpoint was not enforced as a stop/extend decision point. Future launches require predeclared automatic plateau/target-metric rules, earlier checkpoints, and evidence to justify extensions. Retrospective action/amount-token loss analysis is underway to distinguish useful learning from fixed protocol-token loss; different minibatches are not a fixed-validation convergence proof.

Both SFT runs finished40updates and saved final checkpoints: continuation `ckpt_dc82af619ad4`, base `ckpt_30d9913c74b6`. Exit0 confirmed00:54:33/36. Compute wrappers lingered; they were explicitly stopped00:56:02 to release8GPUs without deleting checkpoints.

**GRPO restart submitted:** `train_0dcc5a192e21` / `job_4d0eb2a84133`,6GPUs, queued for released capacity. Samead74parent/20khistoricaldataset/frozenopponents/reward/prompt. Fourtaskgroups×16samples=64rollouts/update (instead of256),100steps,checkpoint5keep20,LR1e-6constant,originalGRPOadvantage/KL/clips,concurrency16,caps24576/32768, in-runevaloff. Server effective config verified optimizerbatch64. **Hypothesis:** retain within-task comparison quality while obtaining real optimizer updates/checkpoints4xsooner. Monitor smaller-batch variance, gradients/KL, legality, reward signal, throughput, and manual held-out checkpoint performance. Do not stop GRPO merely because of infrastructure errors; diagnose/repair them.

Early20update Pete candidate deployments queued: continuation `infer_dd2fdb1ab055`, base `infer_df838d4a9741`. Final steady allocation target:6GRPO+2preserveddeployments+2candidates=10GPUs. No additionalGPUtraining/eval authorized.

**Closed avenues:** Pairedtable-talk validation completed72calls; neither candidate met its predeclared gate. Fold had0/12completevalidtriples; all-in3/12, with zero exact-maxhits in any arm.41missing-toolresponses make effects inconclusive, not provenzero. No further search/training/promotion. Synthetic-reasoning draft was rejected for templated unsupported hand classifications; further generation stopped and no dataset was trained. Keep artifacts only as rejected evidence.

**CPU-only readiness:** Corrected PokerBench v3 (4096cleanpostfloptrain/147fastselect/1582untouchedfinal) fully uploaded/verified after fixing bare action-amount scaling and excluding unsupported source labels. No training queued. Cleanup corpus has four exact recorded concise/factual targets; two concisebutfactuallywrong outputs were rejected. Neither tinycorpus is authorized for GPUtraining without a stronger justification.

## Visibility and startup repair — 01:02 PST

- Action-token audits: `/Users/lance/Documents/pokerbots-pokerbench/experiments/pete-postflop-v1/{base,continuation}-action-ce.json`. All5120managed samples were analyzed separately from fixed protocol/tool syntax. Last10versusprevious10 class-balanced action CE improved21.1%continuation/21.6%base; bet-token CE also continued improving. Coordinator corrected the earlier overconfident convergence answer. This does not remove the missing-checkpoint-decision mistake; different training batches still do not prove held-out poker improvement.
- AC2visible evaluation IDs: `eval_bf31fcaff054` (incumbentsmoke), `eval_521f73148d31` (incumbent32hands), `eval_7353b52d4873` (ad7432hands). The147state postflop/354state preflop diagnostics and fullgame collectors were local and therefore invisible in AC2Evaluations. Userrequested platformvisibility; nextfullgame comparisons will use nativeAC2BYOHevals with named official30handdatasets and zero additional inference GPUs. Do not claim local diagnostics were published.
- GRPO `train_0dcc5a192e21` failed beforeenvironmentready, no optimizer/traces; customer log onlyexit1 anddispatchmainexit80. Engine logs are account-restricted; fullavailablefailureoutput saved. A queued nativeCLIretry under the same failingidentity was canceled before GPUuse. The known working authorized harness credential was reused in memory only, neverprinted/stored.
- Current GRPO **`train_f759c4cb331e` / `job_a865f2cd08f2` is RUNNING**, underjkoumatchingearlierworkingruns: environmentready01:00:36, runstarted01:00:50, samplerstarting01:01:24. Approvedbatch64/checkpoint5/manualevalrecipe unchanged. The working-identity retry repairs startup; exact underlying serverexception remains unavailable, so identity/NFSownership is a hypothesis rather than a provenrootcause.
- Candidate deployments under theotheridentity remain provisioning/restarted. One controlled same-checkpoint/config recreation under the known workingidentity is authorized after teardown/release verification; oldincumbent/frozenopponent deployments stay untouched.

## New-account instruction — 01:08 PST

The user explicitly selected the new `lmathias@berkeley.edu` account and instructed that existing jobs must not be canceled to make the change. All future train/deploy/eval/artifact mutations now use UID 10464 with organization preflight. Existing GRPO and serving jobs remain untouched under their original owners. The local GRPO poller was replaced, with state preserved and read access verified, to monitor through the new account. No cloud job was canceled for this migration.

Current GRPO has genuine graded rollouts and within-group variation. A native AC2 smoke on the ready SFT continuation candidate is authorized using the new account, existing serving capacity, and zero additional GPUs.

## Requested mixed-teacher run and public mining — 01:30 PST

One additional mixed Professor Pete + Chatty Carlos SFT experiment is authorized. Canonical source IDs are `house-professor-pete` and `house-chatty-carlos`. All170 source matches passed engine replay. Training contains7,640 clean unique decisions, exactly3,820 per teacher, including2,710 postflop decisions and780 bets. Selection1,249/final921 are separate whole-match groups; legacy held-out source groups remain excluded from training. Teacher IDs stay in provenance only; targets copy action/amount, not optional table talk or fabricated private notes.

After complete upload verification, the approved base-start pilot will queue under the new account:4GPUs,10updates,batch128,LR5e-6,checkpoint5/10, no rollout/evaluation engine. Teacher-interleaved ordering and first managed-batch teacher participation must be checked. It starts when current GRPO naturally frees capacity; current GRPO is not interrupted. No extension without fixed teacher-balanced selection, legality/retention, and action-token evidence.

The public failure miner is running locally (first snapshot PID42630) every10minutes until09:00, with cached raw bytes/URLs/hashes and explicit first-page coverage. State: `/tmp/pokerbots-public-failure-status.json`; code/report: `/Users/lance/Documents/pokerbots-public-miner/experiments/public-failure-miner-v1/`. Initial sample:8 own matches/368 decisions, one illegal check and two raise-to-bet coercions; generic error tags duplicate those same events and must not be summed as separate failures. No published own table talk in that sample. Private scratchpads/cleanup are not publicly available and are explicitly unsupported. These concrete states are candidates for validity regression tests; they do not justify winner-only strategic labels.

## Checkpoint decision and setup diagnostics — 01:45 PST

RL5 native paired32 (`eval_1712153a22c5`) completed: mean unclipped EV−2.94BB versus parent−0.58BB; paired difference−2.36BB,95%bootstrap interval[−9.34,+1.84], zero invalid decisions. No improvement established; no promotion. A single−100BB river call dominates the tail. Public decision-time review: K-high facing198chips into a4chip pot requires49.5%equity; range/sizing calibration is a hypothesis, not a label derived solely from hidden opponent cards. The review is selection-only and excluded from training. Checkpoint20 is next; stale10cold-start is skipped as an explicit serving-latency ROI decision. Current training/reward/prompt stay unchanged.

Read-only reward audit:1,568 valid EVrollouts;3.89%above+5BB and3.64%below−5BB. Clipping ties298 unequal-EV pairs:2.59%ofall11,506legalwithin-grouppairs, or6.72%of4,433unequal-EVpairs. This establishes saturation, not a demonstrated benefit from changing reward. FrozenopponentGPU is busy but latency stable(~0.70smean/~0.89sp95); wait includes weight refresh/checkpoint effects. No speculative replica or reward change is made.

BaseSFT20 native six-game comparison remains active (`eval_b539897717d8`). First completed matchedgame: place1,+86.5BB,zeroinvalid,30cleanups/30attempts,zerooverlong/cuts; incumbent same seed place1,+15.5BB,40cleanupattempts/9CUT. This is only onegame and not a promotion conclusion. Finalcontinuation40 passed teacher/postflop and preflop diagnostics but its slot was preserved for the promised RLcomparison; all checkpoints/results remain saved.

Verified platform capability notes now live near the top of `TRAINING_RUNBOOK.md` to prevent repeated unsupported-field/endpoint mistakes. The public miner remains active every10minutes; caches, exactrawURLs, hashes, explicitcoverage and unsupportedprivate-data limits are preserved.

## Protocol correction and full-game validation — 02:18 PST

BaseSFT20 six-game selection finished: meanplacement3.333 vsincumbent3.833 (pairedimprovement0.5,95%CI[−0.833,+2.333]); EVgain20.103BB/game withwideCI[−29.147,+61.705]. It is NOT promotion-ready:8/361invaliddecisions(2.22%), plus only39/180correct acceptedcleanupupdates;141unchanged and142wrong-toolcalls. Earlier “short cleanup” statements are corrected: zerooverlongnotes was latency evidence, not correct memory/protocol. Existingbase20 remains fixed as an explicitly imperfect opponent for fair matchedtests; its flaws are not hidden.

RL20's completed32selection: EVgain1.234BB/hand vsparent,95%CI[−0.109,+3.000],0/53invalid. A matched public overbet-state probe gaveparent4folds,RL20twofolds/twocalls,base20twofolds/twocalls; tiny sample, not causal attribution. Four-game development jobs now visible: incumbent `eval_0d1639973dff`,RL20 `eval_41013908bd59`; fresh seeds are separate from sealedfinal6, oldselect6,fast32 andhistoricaltrain. RL20's first completegame had30/30correct acceptedcleanupupdates, not just short outputs. All fourmatchedgames must finish before a conclusion.

The revised requested teacherpilot was verified locally with the actual35Btemplate and remotely withfullmembership/samplechecks before replacing the oldpendingzero-updatejob. Cleanup sources are genuine unchanged TRAINreplies, not fabricatedpublicscratchpads; representation quotes prior context to avoid supervising oldassistantturns and is explicitly documented. Fixed held-out routing gate requirescorrect update_scratchpad, not merely a short response.

## Frozen RL20 selection and final validation — 02:43 PST

All four development pairs finished before freezing RL20. Directional improvement and substantially better cleanup reliability justify a possible monitored canary, not a statistical superiority claim. Separate six-game final is running with pinned opponent/deals and no extra inference GPUs. Functional smoke passed one complete30hand game,0/53invalid,30/30correct accepted cleanup. Workplace probes were legal and silent; actual final outputs will be reviewed within the five-minute promotion budget.

Current entry remains `return of rain man` / `infer_b0f5e9429b7e`. Root browser retries still report `cgWindowNotFound` and browser host unavailable. New-account API exploration was read-only and found no authoritative submit route/schema; no fabricated route, old credential fallback, entry mutation, or job cancellation. Prepared canary remains inactive pending an actual verified promotion.

## Post-GRPO allocation and factual-memory limit — 02:46 PST

After100updates and verified final-save/teardown, budget is mixedteacherSFT4GPUs + four protected serving dependencies + lateGRPO100candidate1GPU + checkpoint40intermediate1GPU =10. Latecheckpoints get one fresh64deal paired selection against frozenRL20 with fixed opponent strata; no sweep of every checkpoint or reuse of the sealed final. Native checkpoint evaluations cannot use customharness in this SDK; known-working standalone deployments/nativeBYOH will be used. No new inference allocations before actual capacity verification.

RL20 cleanup protocol success does not establish factual memory accuracy. A CPU-only audit of150accepted selection/functionalupdates found17with factual-copy mismatches among1370recognizableclaims, mostly oldhistory drift; one currenthand mismatch and one missingcurrenthandclaim. No incumbent factual comparison exists. These are disclosed limitations, not invented training targets or a new perfection gate.

The step85zero-variance alert resolved in subsequent16samplegroups with observed rewardstandarddeviations1.829/0.650/1.291 and healthygradient0.8553. No sustained setupdefect or stoptrigger; recipe unchanged.

## Separate final completed — 02:49 PST

Selected RL20 passed the predeclared numerical legality gate (99.329%, decline0.671pp) and final directional performance was positive, but uncertainty remains wide. Six final placementdifferences[−3,+1,+1,+4,+2,+2] average+1.167places (95%CI[−0.667,+2.667]); EVgain75.366BB/game [−23.208,+170.336]. Cleanup180/180acceptedvs139/180 and41cuts forincumbent. Exactenumfailurestates are receiving4repeatprobes each as final-only regression checks. No checkpoint reselection or training on finalfailures. Actualfinal298outputs were silent with say available; no factualmemorysuperiority claim.

## Final-save failure and recovery hold — 03:00 PST

GRPO reached100optimizerupdates. Customer log states trainer rank1failed during checkpointsave(step100), automaticrestart mayrecover. This is a setup/save failure, not evidence against GRPO or convergence. Step95 is safely persisted. Keep currentjob intact while inspecting supported recovery/status and preserving completefailureoutput; no cancellationbeforepersistence.100deployment and mixedSFTcapacityhandoff temporarily wait for actualsave/teardown. A95fallback would require an explicit recorded decision if100cannotbe recovered.

FinalRL20enumregression8/8legal; preexisting known-enum4/4alsolegal. Eligible monitoredcanary recommendation,111secondworkplacereview,freezeprovenance and finalsummary published undernewaccount in collectioncoll_6dbffac3ae9c. Currentpublicentry remainsincumbent, cachedrank16/rating937 at02:47PST; actualArenaaccess retry stillcgWindowNotFound. No entrymutation.

## Bounded recovery ended; GPU handoff — 03:12 PST

Repeated trainerrestarts (10:59:13and11:07:28UTC) didnot save100or produceoptimizerprogress. Localharness/router/all4shardswerehealthywith0activerollouts, so no speculativeconnectorrestart. Enginefailurelogsarestaff-only; customerlogand95conversionstatus expose no underlyingcause, so filesystem/workererrorremainunclassified.95conversionfailed;40remainsAVAILABLE. Coordinatorauthorizedboundedstuckjobstop, notidentitymigration. TerminalSTOPPED11:11:02after2m05shutdown; no force/repeatedstop/deletion. MixedteacherjobQUEUED11:11:13.90conversionrequestedonce11:11:36asexplicitolder-sourcefallback.

Fresh64RL20baseline maystartafterteardownusingexistingGPUs. New40/conditional90deployments requiremixed4RUNNINGandinitializationproof. Intermediate40slotwillrotatetomixedcheckpoint4afteritsrequestsdrain, forfixed256action/10cleanupgates; historicalstep2controlisdeferred. No modelhotswap APIexists; useknownsupporteddrainedrecreate.

## Teacher run started; capacity verified — 03:13 PST

Mixedteacher `train_41ab837f39e5` / `job_669c09f1d753` RUNNING on4GPUs,environmentready11:11:38UTC,runstarted11:11:53,TP4actorinitializing11:12:18. All7720templateexamples fit8192context;remoteorderedmembershipmatchesinterleaving(first128:63Pete/63Carlos/2cleanup). Actualmanagedbatch participation/target-boundary proofisnext. Protectedserving4+SFT4=8; known40deploymentoneGPUcleared,90secondonlyifconvertedAVAILABLE. Frozen20fresh64nativebaselineissubmittingusingexistingendpoints.

## Step 90 fallback usable — 03:16 PST

Supported conversion for `ckpt_c05e6bad32b6` is AVAILABLE. The authorized second one-GPU evaluation slot can now serve step 90. Step 40 inference `infer_cb17aea4345b` is provisioning; fresh 64-deal RL20 baseline `eval_c53f25c0c5ed` is submitted. Step 95 conversion failed and step 100 is absent; there is no demonstrated global storage-exhaustion diagnosis. The teacher run remains in normal actor initialization with no reported fault.

## Genuine teacher optimization confirmed — 03:20 PST

Mixed SFT published its first two optimizer updates at 11:19:44 UTC: latest loss 0.95634, gradient norm 77.68, both finite. All 256 managed targets passed source-ID, nonempty scaffold, supervised closing-think, exactly-one-tool, and prompt identity-leak checks. Participation: 124 Pete, 131 Carlos, one genuine cleanup target; 31 bet targets. Cleanup token share in these batches is 1.958%, distinct from the full dataset sampling share. This establishes working optimization, not convergence or poker quality. Initialization resolved without a restart. Checkpoint after five updates remains the next behavior gate.

## Bounded opponent-mixture GRPO authorized — 03:30 PST

**Problem:** neither later checkpoint materially improved over step 20 on the same fresh 64 deals. Step 40 gain was +0.144 BB/hand; step 90 gain was +0.670, both with wide intervals and below the prewritten +1 BB advancement threshold. Both were legal with all 64 cleanup updates accepted. No slower full-game expansion is justified.

**Hypothesis:** continuation from the validated step 20 against a second, more aggressive fixed opponent can improve robustness beyond the original passive opponent while retaining legality and cleanup behavior.

**Targeted change:** keep the validated GRPO reward, prompt, optimizer, LR, sampling, caps and six-GPU engine recipe. Train from `ckpt_11e7c430069c` using a fresh-seed TRAIN-only opponent mix. Upload was bounded to 7,500 verified tasks rather than finishing the local 20,000 pool: 3,827 ad74 and 3,673 base20, exactly 1,250 per seat, all stack buckets represented, no known held-out seed/source-match overlaps. Remote membership and sampled content were reconciled after stopping only the local auxiliary uploader. No cloud job was canceled for this data-size change.

**Test and budget:** INITIAL TEN UPDATE HARD CAP, checkpoint after five and ten. The total experiment may reach twenty only through an explicit further ten-update continuation after generated-behavior evidence. The SDK has no public step pause; a continuous twenty-update run could outrun its supposed ten-update decision while checkpoint conversion/evaluation warms. This enforced cap corrects that latency problem before launch. Checkpoint five gets the next available candidate slot; pair against the frozen step 20 selection baseline and inspect both opponent strata, legality and exact cleanup protocol. No final outcomes enter training or checkpoint ranking.

**Success/stop:** at five, diagnose reliability and clear paired regression; at ten, require directional EV improvement across both strata without protocol regression to justify extension. Apply the existing material advancement gate before expensive full games or promotion. Stop on sustained infrastructure/model failure under the saved controller; preserve usable checkpoints. Seed step 20 remains more defensible than unadvanced later checkpoints. Actual Arena incumbent and rollback stay warm. Retiring unused step 20 serving loses immediate candidate readiness, not its weights or an active Arena dependency; it can be recreated if browser access returns.

Teacher SFT finished all ten updates with exit code 0 and both checkpoints registered. Early checkpoint `ckpt_9d62f73b201e` is AVAILABLE; final `ckpt_95bc5ed22ed8` is still converting. All 1,280 targets passed audits: 620 Pete, 651 Carlos, nine genuine cleanup controls. Changing-batch action/amount CE improved modestly; no poker or convergence claim. Fixed generated-action and strict cleanup checks are next. Training evidence is published in collection `coll_6c119f846b5e`.

## New bounded GRPO submitted — 03:32 PST

`train_366541a9d070` / `job_a08388aa07ea` submitted 03:31:11 PST: initial ten-update cap, step 20 seed, verified 7,500-task opponent mix, original six-GPU GRPO recipe, checkpoint five/ten, no evaluation sidecar. New-account identity/org/runtime-secret preflight passed. Effective configuration, real graded rollouts, optimizer updates and checkpoint usability must still be verified.

Unused step 20 and step 40 inference/dispatch objects were verified gone. Step 90 GPU dispatch was gone while its inference frontend finished normal deletion; this is adequate actual GPU-release proof for submitting the new six-GPU job. Actual incumbent/ad74/base20 remain warm. Teacher candidate gets the last one-GPU slot. Measured checkpoint-to-selection latency is approximately 11–13 minutes (conversion 4–5 min, deployment/probe ~3.3 min, paired 64-deal screen ~3.3–3.8 min), confirming why continuous twenty-update training could overrun a supposed ten-update gate.

## Warm-start setup differential and bounded repair — 03:38 PST

The intended mixture pilot `train_366541a9d070` failed before environment-ready: rank-0 container exit 80, customer setup exit 1, zero rollouts. Runtime-secret, owner, dataset and effective configuration checks passed. No identical blind retry was launched. The controlled catalog-BASE GRPO diagnostic `train_c1a9b5d15680` / `job_632c81e0461e` reached environment-ready at 03:34:44, run-started 03:35:00, sampler starting 03:35:32 and four-GPU trainer starting 03:37:24. It is capped at one update and exists solely to discriminate warm-start from general GRPO bootstrap failure. Optimizer/graded-rollout proof is still pending.

The documented serving-sync repair attempt returned permission denied and no path; no retry, old-account fallback or guessed path followed. SDK raw checkpoint and embedded inference metadata did not expose an authoritative converted HF path. Supported managed checkpoint staging/S3 metadata is being investigated with no local weight download, external destination or extra-cost fast transfer. The goal is to restore the exact step-20 weights under the new account, not silently substitute BASE.

Both teacher checkpoints are AVAILABLE. Early `infer_1954005bbb05` passed a real `submit_action` probe; data agent owns fixed 256 + preflop 354 diagnostics and eval agent owns enum/strict cleanup checks, with combined concurrency around four. Actual incumbent/ad74/base20 remain warm. No Arena promotion occurred.

## Teacher early checkpoint fails; final comparison bounded — 03:43 PST

Early five-update checkpoint failed all substantive gates despite 100% legal actions: fixed 256 agreement 45.70% vs incumbent 75.78%, bets 0/27, preflop 114/354 (32.20%) vs 84.46%, and fold recall 18/241. Strict cleanup passed only 5/10: one missing real tool call and four overlong updates; zero wrong-tool calls, enum regression 4/4 legal. No extension, promotion or full-game expansion is justified. These LOCAL diagnostics are published in collection `coll_6c119f846b5e`, with no EV claim.

The already-trained final ten-update checkpoint gets exactly one identical bounded comparison. Early endpoint was retired after requests drained; final endpoint `infer_10d59569a5a5` (checkpoint `ckpt_95bc5ed22ed8`) was requested at 03:40:24 PST on one GPU, with real-tool readiness required before queries. Historical step 2 remains a conditional next control in this same slot, deferred behind any new GRPO checkpoint-five decision.

BASE GRPO has real graded rollouts under the new account; optimizer/save proof is pending. A supported exact-path repair is prepared: source path `/data/ac2/vals-hackathon/train_f759c4cb331e/iter_0000020` comes from a typed server job dependency, not a guessed filename. After the BASE one-update diagnostic saves and releases its six GPUs, one initial-ten-update attempt may use documented `ModelConfig(model=..., checkpoint=absolute_path)` to preserve the same step-20 weights while bypassing registered-ID resolution. No duplicate retry or old-account fallback. Managed serving sync and upload-status APIs denied permission; no further staging calls followed those denials.

## Final teacher policy still fails gates — 03:48 PST

Final ten-update checkpoint improved over five updates, but remains ineligible: fixed-256 action agreement 71.875% (early 45.70%; incumbent 75.78%), bets 3/27 (required at least 7), checks 37/43 (required at least 39). Preflop agreement is 271/354 = 76.55% vs incumbent 84.46%, below the frozen 79.46% retention threshold; call recall is only 1/28. Both diagnostic sets were 100% legal. This is real held-out learning but not sufficient performance/retention, and does not justify relaxing the gates. No extension, promotion or 30-hand expansion. Strict cleanup aggregate is still pending; data-agent requests have drained.

The BASE one-update GRPO diagnostic has all required groups graded and is still initializing its first optimizer step. Aggregate GPU memory continues rising; utilization alone does not prove trainer activity, since earlier utilization could have been the sampler. Ops is applying a five-minute no-progress bound across optimizer, logs and memory before treating it as stalled. No restart solely for an observation timeout.

Provenance correction from existing artifacts: the earlier >75-minute external six-game cohorts were incumbent and frozen ad74, not SFT continuation40. Continuation40 has static bet/preflop evidence and poor matched cleanup stress (1/10), not six-game EV/rank evidence. It cannot inherit the external results. Historical step2 remains the higher-priority deferred control; no old external batch is being rerun.

## Checkpoint-save repair with early proof — 03:54 PST

BASE diagnostic completed optimizer step 1 at 03:46:20 (gradient norm 0.600832, training step 316 seconds), then rank 0 failed saving step 1 at 03:47:04. No checkpoint registered. This proves the save failure also affects a new-account BASE run, not just the old checkpoint or late step 100. Because its diagnostic weights are not a candidate and the known-good step 20 is safe, root authorized an immediate stop after preserving full failure/optimizer evidence. Job STOPPED 03:52:19; no repeat ten-minute recovery wait.

A documented public native option exists: `experiment_cfg.step.no_save_optimizer_state=True`, which saves weights without optimizer state. Reducing the checkpoint payload is a concrete testable repair hypothesis; high memory was observed, but OOM/storage cause is not proven. One repair attempt was submitted as `train_d3a4e8d4cfdb` / `job_7e18dc41d556` at 03:52:44. It uses the exact typed-server step-20 NFS dependency, ten-update hard cap, checkpoint interval one and retention ten so save usability is tested immediately and milestone sources cannot be pruned before conversion. Other policy/GRPO/reward settings are unchanged. Native/server validation accepted all public fields. A separate 20-second failure-log guard preserves full logs and immediately stops on the first save failure. No blind retry if bootstrap fails.

Final teacher checkpoint failed cleanup 1/10 (three missing tool calls, six overlong, none truncated/wrong-tool) despite improved imitation. All requests drained; no continuation. Historical step 2 checkpoint `ckpt_012f74ea70f9` is deploying as `infer_7d4561f17661`, one GPU, for the predeclared fresh64 control only. Future genuine multi-hand TRAIN cleanup collection is CPU-only preparation, not a new launched experiment. Browser retry still finds no accessible window; actual Arena entry remains unchanged.

## Old-source access control and fresh retention data — 04:00 PST

Exact-path step-20 repair `train_d3a4e8d4cfdb` failed pre-environment setup just like registered-ID input (rank 0 exit 80, customer setup exit 1, zero rollouts). No identical retry. It never reached optimizer/save, so it did not test the weights-only option. Own-checkpoint control `train_555fe377c93e` / `job_5cb58e4854d9` was submitted 03:56:27, using new-account SFT final checkpoint `ckpt_95bc5ed22ed8`, one update/save one/keep two and weights-only saving. Source owner UID10464 and catalog format were verified. Environment-ready 03:56:59 and run-started 03:57:15 prove warm-starting is not generally broken. Old-source permissions/staging are a leading differential, not a proven filesystem diagnosis. Its first save is still the critical test.

Historical step2 serving has repeated startup failure with no real-tool proof, despite the recorded available conversion. At the bounded eight-minute point, retirement is authorized rather than holding the GPU indefinitely; this is an inconclusive setup failure, not a quality verdict. No old-account fallback or blind redeployment.

A NEW data-collection experiment is conditionally authorized in that same one-GPU slot: recreate reliable step20 serving, real-tool probe, then two fresh TRAIN-only official30hand games against protected base20 at maxparallel2. If exact source/provenance, factual filtering and long-context coverage work, expand to eight TRAIN plus two SELECT games, max45minutes. Reserve new FINAL seeds but do not launch/read final outcomes before a future student is selected. Preserve exact genuine outputs; no fabricated private notes, winner filtering or existing selection/final notes in training. This targets the demonstrated lack of long-memory coverage. No further SFT is authorized; a future student/parent decision requires a separate targeted plan.

## Public dashboard outage and serving recovery bound — 04:05 PST

Public failure mining attempted its scheduled cycles, but cached team HTML from 03:47 and 03:57 explicitly reports: “The database is unavailable” and “Your account or project has exceeded the quota.” This is the public site's upstream database response, not evidence of our AC2 GPU quota or a model regression. The poller remains alive on its ten-minute cadence and preserves previous raw/cache evidence; no billing change, tight retry loop or parser rewrite is needed. Fresh public rank/routing cannot currently be verified through that site.

Historical2 failed to reach tool-ready; its GPU dispatch was reclaimed and outcome is INCONCLUSIVE_SETUP. The eight-minute intended bound overran by about three minutes during additional status checks; the next serving attempt uses an explicit creation-time deadline rather than delaying reclamation for extra diagnostics. Recreated step20 teacher is `infer_d9d92f687429`, requested 04:00:03 PST; hard real-tool readiness deadline 04:08:03, with no data collection before PASS. Source model, checkpoint and exact outputs remain pinned. Candidate-slot footprint remains one GPU.

Multi-hand collection framework is frozen: two initial TRAIN games, conditionally six more TRAIN plus two SELECT, two FINAL seeds reserved/unlaunched. Two additional TRAIN reserve seeds exist in metadata but are unapproved and cannot be launched. Prior/new seed unions are explicitly separated. Cost cap is 45 minutes on the teacher GPU; no new SFT is authorized. Root's independent IAB recovery attempt also reports browser access host unavailable.

## Working own-account checkpoint path — 04:10 PST

Own-source weights-only GRPO control succeeded: optimizer 12:06:14 UTC (gradient norm 2.671), checkpoint `ckpt_b5a8f86bbb45` registered 12:06:55, customer saved step1 12:06:56, training finished 12:06:58, exit0 12:07:10. Completed wrapper stopped 12:08:38 and released six GPUs. One serving conversion is pending. These combined settings work; this does not prove optimizer payload alone caused earlier failures or that old-source ownership is the sole access cause.

Before spending more RL on the weaker own-family policy, a one-GPU real-tool-ready endpoint and the same fresh64 baseline screen are authorized after conversion. This is quality measurement, not promotion or an extension of the closed teacher SFT experiment. Longer training remains blocked on the result/root decision. A ten-update own-family continuation config is prepared CPU-only, with weights-only save after five/ten; no auto-launch.

Reliable step20 serving `infer_d9d92f687429` passed its real-tool probe at age340.9seconds, before the independent hard deadline, which was canceled. Initial two fresh TRAIN games started in native `eval_0eab37d83222` / `job_e4d260c6c910` at 12:07:07 UTC, verified two-task membership/content, parallel2, fixed base20 opponent. Collection-wide deadline12:52:07. No expansion before provenance/factual/long-context process proof, no FINAL/SFT launch. The working teacher endpoint is again warm for a possible candidate promotion, but actual Arena control remains unavailable.

## Memory collection stopped; grounded offline OPSD probe — 04:29 PST

The initial two TRAIN games completed. Only five unchanged replies retained both visible current facts and a provided verified prior fact; none qualified as useful long-memory targets. Expansion is stopped, so no further six-game rollout tranche or SFT payload follows this failed data hypothesis.

A different, pre-output framework uses genuine incumbent-C Arena cleanup contexts with naturally long incoming notes. A bounded512-row source query returned222cleanup inputs,182unique long inputs after exclusions,16wholematches. The frozen whole-match split has140long TRAIN contexts from13matches and three held-out matches. Source cutoff12:26:48.093798UTC. Original runtime message content is preserved; original Arena tool definitions were not in telemetry, so the new isolated experiment explicitly supplies the published canonical main-tool schema to both student and teacher and does not claim byte-identical original tool definitions.

Preferred test is native OFFLINE OPSD: actual unhinted OWN10 replies sampled on these contexts, same-model teacher with a teacher-only compression/prior-retention hint, and `HintSelection.rollout_prefix_len` masking the full existing history. Contexts are off-policy; fresh reply samples are on-policy for the OWN10 checkpoint. It is not cross-model SFT, does not quote/rewrite prior assistant messages, and does not supervise their old tokens. Authentic complete defective replies may be represented for reverse-KL reweighting; truncated/unrenderable cases are excluded and reported. Managed backend permission/rendering/token masks and teacher benefit remain unproven. The external paid judge is explicitly disabled. No training is authorized yet.

OWN10 probe endpoint `infer_42df4eab0ad2` / checkpoint `ckpt_95bc5ed22ed8` was requested12:27:54UTC on one GPU after genuine source-count proof. A hard eight-minute real-tool guard applies. Up to32paired hinted/unhinted cases are authorized only after factual eligibility and measured token fit; this is at most64model calls, not a new training run. Four existing endpoints remain warm. B5's serving conversion still had no completion at its12:23deadline; no baseline endpoint or longer RL was launched. A passive five-minute status watcher may catch late terminal completion without holding a GPU or retrying conversion.

## Hinted OWN10 memory tests closed; model-only ablation — 04:46 PST

V1 improved compact core-fact coverage (9/10 vs2/10) but failed strict factual acceptance: one invented action, two wrong streets and one overlength reply establish at most6/10 below the frozen8/10 bar. All20 gateway replies ended normally and matched the captured request/output. V2, on ten fresh TRAIN contexts, constrained the hint to verified board/stacks and forbade action prose; four hinted replies still exceeded1500characters and all retained forbidden narrative. It also fails at most6/10. Forty total calls, no retries/rewrites/training. Actual emitted reasoning was preserved, not fabricated. Managed OPSD permission/masks remain untested because the behavior gate failed first.

One final MODEL-only ablation is authorized on the exact V2 cases/hints/tools/decoding, using reliable RL20 rather than OWN10: twenty calls, total60<=original64. Same strict8/10 and at least3-case gain requirement. No more prompt variants; if both models fail, close this memory avenue. The OWN10 endpoint may be reclaimed after all requests drain; its weights remain preserved. Step20 remains warm.

A single documented SGLang model-info GET on the existing step20 backend returned404; no route variants, broad server-info/env read or guessed converted path followed. The distinct user-facing SDK `checkpoints.get_urls(..., format='serving')` DID accept a request under lmathias and reports STAGING. This provider-managed route may expose an authoritative HF object manifest for an own-namespace import of the exact weights. No signed URL is printed/persisted, no bulk weights reach the Mac, no external destination/paid fast-transfer option is used. Poll60seconds for15minutes then passively; no import/training mutation before source/cost review. Internal sync/upload-status denials do not establish that the public download API is denied.

## Late conversion completion and revised source diagnosis — 05:01 PST

Passive monitoring caught `ckpt_b5a8f86bbb45` AVAILABLE at12:55:52UTC, long after the active15minute wait ended. This validates retaining observation of a nonterminal handle without retrying conversion or allocating a waiting GPU. Conversion took about49minutes, so future hard-cap checkpoint decisions must account for this variable delay. Baseline deployment `infer_db04467416e4` was submitted13:00:27, oneGPU/newaccount, hard8minute real-tool readiness then the existing fresh64 comparison. It is a baseline of the currently trainable own family, not an approved promotion.

Read-only metadata shows old and new runs all used the SAME cluster/infra `clr_fd567510d260`; old owner UID10457 vs new10464. Cross-cluster NFS placement is therefore weakened as the explanation; source access/format remains unresolved. The public serving20 download initially accepted STAGING, then returned404 with safe detail `Job not found: job_95acd06a0ec3`. A public include-deleted job lookup also returned404. This names a missing/invisible staging/provider job, not proof that the checkpoint is missing. No bulk download/import, endpoint variants, signed-URL disclosure or identity fallback followed.

The final RL20 hint ablation failed eight overlength cases. Wire, official HF rendering, and actual response usage all confirm the hint was present: prompt-token increases289–322 on all ten pairs. The memory-hint avenue is closed after60total calls; no training occurred. OWN10 endpoint and dispatch were reclaimed, source weights preserved. Step20 remains warm and protected.

A new CPU-only bounded attack-test setup repairs the earlier invalid GEPA test by using known-ready ad74/base20, real tools and certified royal-flush decisions where folding is dominated. It is a causal synthetic decision probe, not a full-game/leaderboard quality claim. First four no-SAY setup calls are authorized only after conservation/reachability checks; no training or live harness change. Full development matrix remains gated on calibration/root review.
