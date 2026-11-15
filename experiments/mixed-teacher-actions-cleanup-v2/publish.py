import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;c=working_client();identity=preflight_identity(c);run=json.loads((R/'run.json').read_text());slug='mixed-pete-carlos-actions-v1';coll=c.collections.get_by_slug(slug=slug)
preflight_identity(c);c.collections.add_train_runs(collection_id=coll.id,ids=[run['train_id']])
preflight_identity(c);c.collections.update(collection_id=coll.id,name='Mixed Pete + Carlos BASE pilot — protocol-retention revision',description='ONE requested experiment. Original queued action-only run stopped at0updates for observed cleanup routing bug; replacement preserves7640actions+80copiesof4genuinecleanupTRAIN.10updates/checkpoint5and10. No runningjobinterrupted. New receipt supersedes original queued README; holdsplitsunchanged.')
(R/'REPLACEMENT_README.md').write_text(f'''# Protocol-retention revision: current mixed-teacher pilot

Current run `{run['train_id']}` / job `{run['job_id']}`, lmathias@berkeley.edu UID10464. Same BASE model,4GPUtrainer,batch128,LR5e-6,10updatecap,checkpoints5/10,zero rollout/evalengines. Natural capacity queue; GRPO untouched.

Supersedes original QUEUED_PILOT_README: old `{run['replaces']}` was confirmed pending with0optimizerupdates and its computejob stopped before replacement submission. This is a protocol bugfix,not identitymigration,and no secondcontrol was launched. Old config and receipts remain preserved.

Dataset7,720: unchanged3,820legalPeteactions+3,820legalCarlosactions and80samplingcopies of4genuine validated own-model TRAINcleanup replies. Teacher identities remain provenanceonly. Cleanupcontents unchanged; no inventedpublicscratchpads. Prior own assistant/toolhistory explicitly quoted as usercontext,so only final update_scratchpad is supervised; runtime representation differs. Official35B template audit all7,720passes, cleanup4.629%targettokens. Fullremote membership and12sampledpayloads verified.

Samefixed256selection and original whole-match/deal selection/final holdouts. Add strict10input heldoutcleanup gate:>=9exact valid update_scratchpad,zero submit_action duringcleanup,contents-onlystring<=5000; factualcorrectness separatelyrequired. Shortnessalone cannotpass. Noautomaticextension. Firstmanagedbatch provenance/tool/mask audit monitorPID87020, zeroadditionalGPU.
''')
files=['REPLACEMENT_README.md','EXPERIMENT.md','prepared.json','prefix-balance.json','local-template-audit.json','remote-audit.json','STOP_AND_EXTENSION_POLICY.json','run.json']
p=R/'publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'slug':slug,'artifacts':{}}
for name in files:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n')
assert coll.id in c._require_api().request('GET',f'/train/{run["train_id"]}').json()['collection_ids']
receipt.update(verified_train_membership=True,identity=identity,monitor_pid=87020);p.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
