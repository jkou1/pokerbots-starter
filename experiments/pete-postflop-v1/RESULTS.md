# Initial pilot evidence

Continuation:train_e3fba0323bd2 fromckpt_51eee61470f7,LR2e-6. Independent base control:train_4cc69b58d8e9,LR5e-6. Same1667records,seed42,batch64,40updates/checkpoint20. No poker improvement claimed from loss.

Warmstart was audited beyond tags: v2 requestedconfiguration includes the incumbent checkpoint, runtime staged source differs from base, and64/64 initial prompt+target token hashes match across runs while initial per-sequence CE differs materially (continuation0.027256mean,base1.033634). First aggregate training losses0.0321547 versus1.0245289 corroborate different initial weights. Effectiveconfiguration omitsfrom_checkpoint on both runs; that omission is not proof of failed restoration.

All128 first-batch managed targets pass the combined-boundary check: current student_prompt ends`<think>\n`; target starts`Tool call follows.`, with supervised`</think>` before tool invocation. The older canonical audit wrongly required another newline in the target and was fixed separately on audit-boundary commit5db4fe7, with7focused tests passing.

Early iteration19 checkpoints:continuationckpt_138f27148eef,baseckpt_23b6b6239f26. Both serving-conversion states becameavailable at2026-11-15 08:54UTC. Conversion-only nativepromote was used; convert endpoint was permission-denied. No inference deployments were created by this agent.

Checkpoint selection uses heldout postflop147 and official paired poker games; final103 remains untouched. Selection diagnostic gate:>=10/39teacherbets,>=69/77teacherchecks,>=99%legal plus preflop retention. Full-game cleanup needs separate checks because existing policies generate overlong updates. Workplace-appropriate table talk check is required before any promotion.
