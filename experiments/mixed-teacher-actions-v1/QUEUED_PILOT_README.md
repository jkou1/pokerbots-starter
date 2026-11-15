# Mixed Pete + Carlos BASE pilot

Actual run:train_93e592d258f9, ownerlmathias@berkeley.edu /UnixUID10464. One4GPUtraining replica,10updates,batch128,LR5e-6,checkpoints atiterations4and9. No rollout/eval engines, no automatic extension. It queues behind current GRPO; no existing job is interrupted.

Training7,640unique actions:3,820per teacher.170/170source matches fully replayed; no illegal/fallback teacher target retained. Whole-match/duplicate-deal groups are split before mixing, and prior frozen selection/final source matches are excluded from training. Teacher identities are provenance only, absent from student prompts. No say,private reasoning,or cleanup targets are copied.

Fixed fast selection256records,128per teacher. Current incumbent LOCAL reference:75.78%action agreement,100%legal,0/27teacherbets and43/43teacherchecks. This is a local inference diagnostic published as an artifact,not a native Eval run. Final921records remain untouched for checkpoint choice.

The pre-submission framework and numeric stop/extension policy are separate artifacts. At10updates the pilot stops naturally; continuation requires fixed-selection,legality/retention,action-only CE and official poker evidence. No blind40-update budget.
