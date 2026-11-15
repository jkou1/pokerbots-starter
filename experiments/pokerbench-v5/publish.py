"""Native project collection: actual run plus clearly LOCAL aggregate evidence."""
import json,sys,hashlib
from pathlib import Path
import httpx
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;c=working_client();identity=preflight_identity(c);slug='pokerbench-v5-reconciled-knowledge-pilot';run=json.loads((R/'run.json').read_text())
try:coll=c.collections.get_by_slug(slug=slug)
except httpx.HTTPStatusError as e:
 if e.response.status_code!=404:raise
 preflight_identity(c);coll=c.collections.create(slug=slug,name='PokerBench V5 ad74 coverage pilot —20update cap',description='One actual4GPU SFT run,3499postflop/387preunique,rounded-potlabeluncertainty,LOCAL frozen parent imitation (not nativeEval/EV).Weights-onlysave10/20,no extension.')
p=R/'publication.json';receipt=json.loads(p.read_text())if p.exists()else{'collection_id':coll.id,'collection_slug':slug,'identity':identity,'train_id':run['train_id'],'artifacts':{}}
if not receipt.get('train_linked'):preflight_identity(c);c.collections.add_train_runs(collection_id=coll.id,ids=[run['train_id']]);receipt['train_linked']=True;p.write_text(json.dumps(receipt,indent=2)+'\n')
source=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training/catalog-base-drgrpo-short-v1/v5-train-money-scope-receipt.json');(R/'independent-money-scope-receipt.json').write_bytes(source.read_bytes())
local={'record_type':'LOCAL diagnostic, not nativeEval or pokerEV','select136':json.loads((R/'parent-baseline/select136-summary.json').read_text()),'pre354':json.loads((R.parent/'pokerbench-v4/parent-baseline/preflop-select354-summary.json').read_text()),'cleanup10':json.loads((R.parent/'pokerbench-v4/parent-baseline/cleanup-stress10-summary.json').read_text()),'cached41_wire_proof':json.loads((R/'parent-baseline/cached41-wire-reuse-proof.json').read_text()),'all95fresh_requests_drained':json.loads((R/'parent-baseline/complete.json').read_text())['all_requests_drained']};(R/'LOCAL_PARENT_REFERENCE.json').write_text(json.dumps(local,indent=2)+'\n')
for name in ['README.md','EXPERIMENT.md','manifest.json','boundary-audit.json','upload-receipt.json','frozen-gates.json','proposed-ad74-config.json','run.json','LOCAL_PARENT_REFERENCE.json','independent-money-scope-receipt.json','primary-EV-screen-policy.json','first-managed-batch-proof.json','training-audit-summary.json']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n');print(name,a.id,a.state,flush=True)
actual=c.artifacts.list(collection_id=coll.id,limit=100);assert{x['id']for x in receipt['artifacts'].values()}<={x.id for x in actual};receipt['verified_membership']=True;p.write_text(json.dumps(receipt,indent=2)+'\n');print('collection_verified',coll.id,flush=True)
