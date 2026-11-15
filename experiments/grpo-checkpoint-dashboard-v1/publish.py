"""Publish read-only GRPO checkpoint diagnostics; no sealed outcomes or raw traces."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
import httpx
sys.path.insert(0,'/tmp')
from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent
H=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training/pokerbots-history-selfplay-ad74-v1')
E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments')
SLUG='grpo-checkpoint-decisions-20261115'
IDS=['eval_1712153a22c5','eval_a62651277efa','eval_0d1639973dff','eval_41013908bd59']
c=working_client();identity=preflight_identity(c)
meta={}
for ident in IDS:
 d=c._require_api().request('GET',f'/eval/{ident}').json()
 assert d['project_id']=='prj_ba36d29befaf'
 meta[ident]={k:d.get(k) for k in ['name','status','project_id','project_name','dataset_names','created_at']}
train=c._require_api().request('GET','/train/train_f759c4cb331e').json()
assert train['project_id']=='prj_ba36d29befaf'
summary={}
for step in ['step5','step20']:
 p=E/'rl-checkpoint-selection'/step/'summary.json';d=json.loads(p.read_text())
 assert d['candidate']['status']=='succeeded' and d['paired_tasks']==32
 summary[step]={k:v for k,v in d.items() if k not in ['candidate_tasks','parent_tasks']}
clip=json.loads((H/'reward-clipping-diagnostic.json').read_text())
clip={k:v for k,v in clip.items() if not k.startswith('examples') and k!='group_examples'}
assert abs(clip['tie_pair_fraction']-.025899530679645403)<1e-10
assert abs(clip['tie_fraction_of_unequal_EV_pairs']-.06722309948116399)<1e-10
through=json.loads((H/'frozen-opponent-throughput-diagnostic.json').read_text())
through={k:v for k,v in through.items() if k!='raw_recent_rows'}
report={'captured_at':datetime.now(timezone.utc).isoformat(),'identity':identity,'train_id':'train_f759c4cb331e','native_eval_metadata':meta,'completed_single_hand_selection':summary,'development_status':'Pending at metadata capture; linked for visibility, no development scores published as final.','reward_clipping_read_only':clip,'throughput_read_only':through,'scope':'Single-hand selection screens are not 30-hand placement or Arena rating. Clipped reward is not poker EV. No sealed final queried. No raw private traces uploaded.'}
(R/'CHECKPOINT_DECISIONS.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'READ_ME_FIRST.md').write_text('''# GRPO checkpoint decisions — native selection and read-only diagnostics

Training: `train_f759c4cb331e`. Native eval links are attached to this collection. Development jobs are pending at this snapshot; their outcomes are deliberately omitted until complete.

| Completed single-hand paired selection | Tasks | EV difference vs parent (BB) | Paired bootstrap 95% CI | Invalid policy decisions |
|---|---:|---:|---|---:|
| Step 5 | 32 | -2.3594 | [-9.5625, +1.7813] | 0 / 50 |
| Step 20 | 32 | +1.2344 | [-0.1094, +3.0000] | 0 / 53 |

These are fixed-deal/seat/opponent single-hand selection screens, not official 30-hand placement or Arena rating. EV may fall back to realized return for unsupported side pots. Both intervals include zero; this does not establish a leaderboard improvement. Clipped training reward is a separate signal, not poker EV.

Read-only clipping snapshot: 1,568 valid-EV rollouts out of 1,577 scored. Different-EV reward ties affect **298 / 11,506 = 2.59% of all legal within-group pairs**, or **298 / 4,433 = 6.72% of unequal-EV pairs**. Groups can span generated policy versions. This is descriptive saturation, not causal proof of failure.

Read-only throughput snapshot (12 steps): waiting 488.26s versus training 349.69s, raw waiting fraction 58.27%. Excluding post-checkpoint timing, 10 steps show 53.09% raw waiting. Waiting overlaps weight-update work; these figures are not a causal attribution solely to the frozen opponent.

No official metrics were modified. No sealed final outcomes, credentials, or raw private conversations were uploaded. `CHECKPOINT_DECISIONS.json` contains aggregate evidence and metadata only.
''')
try:coll=c.collections.get_by_slug(slug=SLUG)
except httpx.HTTPStatusError as e:
 if e.response.status_code!=404:raise
 preflight_identity(c);coll=c.collections.create(slug=SLUG,name='GRPO checkpoint decisions — Nov15',description='Completed native paired selection, pending development links, and read-only clipping/throughput diagnostics. No final outcomes or raw private traces.')
preflight_identity(c);c.collections.add_train_runs(collection_id=coll.id,ids=['train_f759c4cb331e'])
preflight_identity(c);c.collections.add_eval_runs(collection_id=coll.id,ids=IDS)
p=R/'publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'slug':SLUG,'artifacts':{}}
for name in ['READ_ME_FIRST.md','CHECKPOINT_DECISIONS.json']:
 sha=hashlib.sha256((R/name).read_bytes()).hexdigest()
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=SLUG)
 receipt['artifacts'][name]={'id':a.id,'sha256':sha,'state':a.state}
 p.write_text(json.dumps(receipt,indent=2)+'\n')
for kind,ident in [('train','train_f759c4cb331e')]+[('eval',x) for x in IDS]:
 assert coll.id in c._require_api().request('GET',f'/{kind}/{ident}').json()['collection_ids']
receipt.update(verified_membership=True,identity=identity,collections_url='https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/collections')
p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
