# Poker bot training strategy

This is the working strategy for one arena-compatible model, trained in stages. It records the choices made in our conversation; [TRAINING_RUNBOOK.md](TRAINING_RUNBOOK.md) describes the experiments and execution order. The data pipeline and training/evaluation commands are now implemented. Execution status and commands are recorded in [TRAINING_RUNBOOK.md](TRAINING_RUNBOOK.md); implementation does not imply that a trained checkpoint has passed the promotion gates.

The active experiment starts from **base `Qwen/Qwen3.6-35B-A3B` weights**, as requested by the user, and combines refreshed Pete pre-flop demonstrations with starter-deal post-flop/cleanup replay. It uses no step2 or distillation parent checkpoint. See [DATA_STRATEGY.md](DATA_STRATEGY.md) for the current experiment and [PETE_SFT.md](PETE_SFT.md) for the first run's thinking-boundary failure. The user explicitly requested committing and pushing the implementation before the corrected run's evaluation finishes. Model promotion still requires a real official-format evaluation. Earlier checkpoint-based pilots remain historical comparisons.

## Objective and stage boundaries

- Optimize final placement in official six-seat, 30-hand games. Use chip returns as a lower-cost training signal and diagnostic.
- Establish reliable betting before optimizing outgoing table talk.
- **Pre-flop:** learn whether and how to continue with a hand, including folding, checking, calling, raising, sizing, and responding to further raises. Emit no table talk.
- **Post-flop:** continue sound betting on the flop, turn, and river; add outgoing table talk only when experiments demonstrate a benefit.
- **Incoming talk:** aim to make betting decisions independent of all opponents' chatter, including claims about their cards. This applies before and after the flop and during scratchpad cleanup.
- Deliver one model descended from `Qwen/Qwen3.6-35B-A3B`. The arena owns its prompt, so the strategy must be learned in the weights.

## Pre-flop: principles plus Professor Pete

### Starting principles

Teach these as a starting policy that outcome-based training can improve:

> Play selectively and account for position. Prefer stronger hands in early position and widen selectively in later position. Give raises a purpose: value, isolation, or a justified steal. Call when the price, effective stacks, position, and likely ranges support it. Check when continuing is free. Reassess after a raise or re-raise rather than treating entry into a pot as a commitment. Keep outgoing table talk empty before the flop. Base decisions on game facts and betting behavior, independently of chatter.

The inputs are our hole cards, position relative to the button and blinds, live players, effective stacks, pot, price to call, legal raise range, and preceding betting actions. Later in a game, observed betting tendencies and the remaining hands also matter. Do not reduce the policy to a hand-strength threshold or a binary play/fold classifier.

Cover unopened pots, limpers, facing an open raise, blind defense, re-raises, multiway pots, short stacks, and shoves. Include repeated decisions within the same pre-flop betting round. Training should cover pairs, suited and offsuit hands, connected hands, marginal hands, and clear folds across every seat. Preserve naturally distributed deals in evaluation so oversampling interesting hands cannot inflate results.

### Learning from Professor Pete

The source is the public [match archive](https://www.pokerbots.ac/matches), supplied by the user. Collect the raw JSON for every available match into an archive, then derive the training datasets from it. Professor Pete is identified by entry ID `house-professor-pete`, rather than by display-name matching. The inspected match identifies it as a house bot; it does not expose a deployment or checkpoint version for Pete. Its current leaderboard position has not been independently verified.

Source inspection on November 14, 2026 (Pacific time) verified a paginated match listing and a **Raw JSON** link on an [example Pete replay](https://www.pokerbots.ac/matches/m_20261115t024346_941971). That sample uses schema `vals-arena.match/1`, contains 30 hands and 30 Pete pre-flop decisions, and includes each dealt player's hole cards. The frozen collection now contains all 130 matches visible at the collection cutoff. All 130 passed replay validation, producing 1,598 Pete pre-flop examples: 1,328 train, 174 selection, and 96 evaluation. The training split is uploaded as `pokerbots-pete-v1-train`; source bytes and derived splits live under the ignored `data/arena/` directory.

Archive every player's records, but use **only Pete's pre-flop decisions** as Pete imitation targets. Other players' actions provide the betting context and opponent analysis. Post-flop records can supply betting situations and real table-talk examples for separate experiments; do not automatically treat every player's decisions as good demonstrations. Keep losing matches and folds alongside wins.

### Match JSON collection and conversion

Follow match-list pagination, deduplicate by match ID, open each replay, and follow its actual Raw JSON link. The inspected JSON link points to public blob storage and includes an opaque suffix; do not construct download URLs from match IDs. Save the original bytes and a manifest containing match ID, replay URL, raw URL, fetch time, content hash, schema, runner version, match kind, and status. Use a fixed collection cutoff and freeze the manifest for each dataset release; do not continuously add live matches to an existing evaluation split.

The inspected schema differs from the training harness's own game logs:

| Source location | Use |
| --- | --- |
| Top-level `seats[].entry.id` and `seats[].seat` | Resolve Pete's seat separately in every match |
| `hands[].players[].hole_cards` and `starting_stack` | Our decision-time private cards and initial stacks; never reveal other players' cards to the model |
| Hand button, `blinds`, and action prefix | Reconstruct position, live players, commitments, stacks, and legal actions |
| `actions[].street`, `seat`, `action`, `amount`, `pot_before`, `to_call`, and `board` | Select pre-flop decisions, validate replay state, and build action/sizing targets |
| Action `tool_args` and failure/coercion flags | Compare requested and applied actions; exclude corrupted or automatic decisions |
| `say`, final board, results, and stacks after the hand | Separate chatter corpus and evaluator-only outcomes |

Replay the recorded action prefix through a compatible engine to recover legal bounds, including raises that do not reopen betting, side pots, and short stacks. Validate reconstructed pot, call price, actor, board, and stack against the JSON. Emit one example immediately **before** applying Pete's action. Do not use the current action's `stack_after`, later actions, final board, or match outcome as input. If a format or runner version cannot be replayed correctly, quarantine its matches rather than approximate missing legal state. Record the adapter version.

Skip Pete targets marked fallback, coerced, format error, AFK, timeout, token cap, sat out, error, or scripted, and reject mismatches between requested and applied actions. Earlier valid applied opponent actions still form the game context. Pete's own `say` is omitted from pre-flop training targets to preserve our silent pre-flop strategy. Private scratchpads and model reasoning are absent from the inspected public JSON; do not fabricate them.

Deduplicate before assigning whole matches to deterministic 80% training, 10% selection, and 10% held-out splits. Keep duplicate/replayed deals together when detectable. All hands, extracted decisions, and talk perturbations from a match inherit its split. Report total matches, hands, Pete decisions, rejected records, and coverage by position, hand class, stack depth, and betting situation. Corpus size and coverage must be measured after ingestion rather than assumed from the number of matches.

Use the available source as follows:

| Available evidence | What we can learn |
| --- | --- |
| Decision records with Pete's hole cards, decision-time state, and chosen action | Supervised examples of pre-flop action and raise sizing |
| Callable endpoint that accepts the game observation | Fresh demonstrations on our training situations; repeat selected situations to observe mixed behavior |
| Public replays without Pete's hole cards | Position-specific participation, aggression, sizing, and reactions to raises; insufficient for hand-specific imitation labels |
| Summary statistics or leaderboard position alone | A comparison target; insufficient to reconstruct the policy |

For each usable demonstration, retain the source game and bot version, decision-time observation, action, and amount. Reconstruct only information available at that decision. Exclude future board cards, subsequent actions, outcomes, and opponents' private cards from model inputs. Keep Pete's private cards only when they are legitimately available as the acting player's input. Do not invent private scratchpad contents or explanations for its decisions. If its missing memory materially changes the observation, use the record for aggregate analysis instead of treating it as a fully observed teacher example.

Split by source game before extracting examples, and deduplicate repeated replays. Preserve folds and losing hands: winning hands alone are a biased sample. Check each target against the legal actions and the harness's raise-to convention. Remove incoming chatter from the canonical imitation input; uncertain examples that may reflect talk manipulation stay out of the initial imitation set.

The initial combination is sequential:

1. Start from base weights and supervise the 1,328 validated Pete pre-flop action/amount targets, without a replay mixture in this first experiment.
2. Compare checkpoints with base on the fixed selection records and paired poker games. Keep the selected policy as the parent for later work.
3. Use position-aware principles for diagnosis and optional later distillation, then refine betting with outcome-based RL. Use clean policy replay when later stages need to preserve learned behavior.

Learn Pete's action frequencies and sizing rather than copying its wording. When Pete and the principles disagree, record the disagreement and resolve it through held-out poker performance. Teacher agreement is a diagnostic, not the final reward.

If some matches omit Pete's cards or fail replay validation, retain them only for supported aggregate analysis. If ingestion yields insufficient qualified demonstrations, proceed with the principles-only baseline and label the Pete branch **awaiting usable demonstrations**. Do not describe that checkpoint as having learned Pete's strategy.

## Betting curriculum before outgoing talk

Keep the official tool schema, including optional `say`, throughout training. Silence means an omitted or empty `say` value.

| Stage | What learns | What stays fixed for attribution |
| --- | --- | --- |
| Baseline | Nothing; measure the base model | Rules, deals, seat rotation, and opponent versions |
| Pete imitation from base | Pre-flop action and sizing through supervised training | Frozen source matches and held-out observations; no replay mixture in the first run |
| Optional pre-flop principles | Pre-flop decision replies through OPSD after diagnosing the imitation result | Other streets receive no targeted distillation loss |
| Pre-flop RL | Pre-flop action decisions | A frozen checkpoint handles our post-flop continuation |
| Post-flop betting RL | Flop, turn, and river betting decisions | A frozen checkpoint handles our pre-flop decisions; outgoing talk stays empty |
| Talk defense | Decisions and cleanup under varied incoming messages | Clean poker targets and decision-time game facts |
| Outgoing talk | A message at a nominated post-flop decision | The selected betting policy, including the action paired with that message |
| Integration | One deployable policy through full-hand practice | Retained clean and adversarial evaluations gate promotion |

Street-specific RL requires training-harness routing so only the selected streets call the training relay; the other streets and cleanup call the frozen checkpoint. Both routes must preserve the same complete hand conversation and scratchpad state. Ordinary full-hand GRPO updates the whole policy and must not be presented as isolating pre-flop learning. All final evaluations use the official observation and action rules without training-only routing or strategy hints.

For early RL, retain the starter reward: valid hands receive `6 + clip(ev_bb, -5, 5)`, and model-caused failures receive 0. Its EV adjustment averages eligible all-in runouts; it is not a solver value for every action and does not remove all poker variance. Log unclipped returns and the fraction of saturated rewards. Do not add bonuses for playing more hands, raising, matching Pete, or making another bot fold.

The post-flop betting baseline should account for made hands, draws, board texture, opponent ranges inferred from actions, position, pot odds, effective stacks, value sizing, and justified bluffs. Winning one realized hand does not make every decision in that hand correct. Hidden cards may support evaluator-only diagnostics but must never enter observations or dictated policy rules.

## Incoming talk: learn independence

Build groups of the same decision state with silence, ordinary chatter, truthful and false hand claims, direct action requests, claimed authority or rule changes, distractions, and repeated messages. Change only incoming talk. Apply the official sanitizer before presenting any message.

Use a clean, validated poker decision as the common action-and-amount target for the group. Train on clean and perturbed versions, retaining a 50:50 clean/perturbed sampling mix initially. Choose perturbation categories uniformly within the perturbed half. Keep whole message families and source games separate across training and evaluation.

Cover pre-flop, every post-flop street, earlier messages still present in the conversation, and after-hand cleanup. Scratchpad targets should retain verified game facts and betting observations without copying chatter, adopting its instructions, or treating card claims as observations. Include delayed tests where a message appears in one hand and the bot makes decisions in later hands. Also test whether the bot follows its own outgoing attack text when that text remains in context.

Measure action and sizing changes at identical states separately from chip returns. Deterministic testing should approach identical outputs; stochastic testing should compare distributions and repeated-call noise rather than require identical sampled actions. Consistency alone is insufficient: the bot must retain good clean poker performance.

## Outgoing talk: measure the added poker value

Start with silence, ordinary poker chatter, and a small catalog of messages aimed at inducing folds, calls, or excessive aggression. Include direct instructions and authority claims as experimental categories. Messages must survive the actual lowercase, character filtering, and 70-character limit. Do not assume a long or specially formatted injection will reach another bot intact.

At a selected post-flop decision, first choose the action and amount using the frozen betting policy. Compare continuations with that same action and either silence or a candidate message. Restore the same pre-decision engine and conversation state in each branch, including private memory where present. Preserve deck/runout randomness and opponent versions; use repeated continuations to account for model sampling. Future actions follow the same fixed policy and may differ as the game develops.

Measure changes in opponents' actions, our returns, invalid-action rates, and later scratchpad effects. A change counts as useful manipulation only when it improves our poker outcome. A fold can be bad when we wanted a weaker hand to call; more calls can be bad when we are bluffing. Use action-change rates for diagnosis and matched return differences for choosing messages.

If the catalog shows repeatable gains, train a contextual message policy. Its targeted task emits exactly one `submit_action` containing the already selected legal action/amount plus `say`; changing the fixed action invalidates the training sample. All other decisions use the frozen betting policy. This requires a training-only experiment runner and grader. Start with the existing chip-return reward and estimate the incremental benefit against matched silence controls; do not reward compliance by itself.

Include silent and resistant opponents as controls and hold out opponent versions and message families. Compare against ordinary chatter as well as silence to distinguish instruction-following effects from ordinary poker signaling. Train the final model on successful action-and-message targets using the original official observations, with the fixed-action training hint removed. Then verify that defense and clean betting have survived. Keep silence as the default if outgoing talk has no demonstrated benefit.

## Final selection and revision

Select checkpoints on a selection split, then evaluate the chosen candidate once on a separate held-out split. Compare the base model, principles-only bot, principles-plus-Pete bot when available, betting baseline with defense, and final talk-enabled bot.

The primary final metric is placement in official 30-hand games. Report mean placement, first-place frequency, bust frequency, chip returns, and invalid decisions. Pair candidates by game seed, policy seat, and opponent configuration; compute uncertainty over whole games. Report EV-adjusted chip returns as a secondary metric and do not infer arena-rating gains from single-hand reward alone.

Each strategy revision records the dictated change, hypothesis, affected stage, teacher/source version, dataset IDs, parent checkpoint, opponent versions, and selection results. Change one strategic hypothesis at a time. The next revision can replace the starting principles in plain English; implementation work should translate that revision into hints, training situations, and evaluation cases without silently changing its intent.
