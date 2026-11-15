# Protocol-retention revision: current mixed-teacher pilot

Current run `train_41ab837f39e5` / job `job_669c09f1d753`, lmathias@berkeley.edu UID10464. Same BASE model,4GPUtrainer,batch128,LR5e-6,10updatecap,checkpoints5/10,zero rollout/evalengines. Natural capacity queue; GRPO untouched.

Supersedes original QUEUED_PILOT_README: old `train_93e592d258f9` was confirmed pending with0optimizerupdates and its computejob stopped before replacement submission. This is a protocol bugfix,not identitymigration,and no secondcontrol was launched. Old config and receipts remain preserved.

Dataset7,720: unchanged3,820legalPeteactions+3,820legalCarlosactions and80samplingcopies of4genuine validated own-model TRAINcleanup replies. Teacher identities remain provenanceonly. Cleanupcontents unchanged; no inventedpublicscratchpads. Prior own assistant/toolhistory explicitly quoted as usercontext,so only final update_scratchpad is supervised; runtime representation differs. Official35B template audit all7,720passes, cleanup4.629%targettokens. Fullremote membership and12sampledpayloads verified.

Samefixed256selection and original whole-match/deal selection/final holdouts. Add strict10input heldoutcleanup gate:>=9exact valid update_scratchpad,zero submit_action duringcleanup,contents-onlystring<=5000; factualcorrectness separatelyrequired. Shortnessalone cannotpass. Noautomaticextension. Firstmanagedbatch provenance/tool/mask audit monitorPID87020, zeroadditionalGPU.
