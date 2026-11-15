"""Publish only aggregate LOCAL diagnostics and preparation receipts, never raw traces."""
import json,sys,hashlib
from pathlib import Path
import httpx
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;O=R/'parent-baseline';assert json.loads((O/'complete.json').read_text())['all_requests_drained'];summary={'record_type':'LOCAL parent reference, not native Eval or poker EV','is_ac2_eval_run':False,'parent':json.loads((O/'lock.json').read_text()),'checks':{n:json.loads((O/f'{n}-summary.json').read_text())['summary']for n in ['pokerbench-select41','preflop-select354','cleanup-stress10']},'caveat':'Cleanup shape/length checks alone do not establish factual or useful memory. No FINAL queried and no training launched.'};(O/'LOCAL_PARENT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');c=working_client();identity=preflight_identity(c);slug='pokerbench-v4-consistent-knowledge-pilot'
try:coll=c.collections.get_by_slug(slug=slug)
except httpx.HTTPStatusError as e:
 if e.response.status_code!=404:raise
 preflight_identity(c);coll=c.collections.create(slug=slug,name='PokerBench V4 consistent-only knowledge pilot — prepared',description='Verified datasets and LOCAL old-SFT ad74 baseline. Not a native Eval record; no training run submitted. Cash-source solver knowledge transfer, sealed final untouched.')
p=R/'baseline-publication.json';receipt=json.loads(p.read_text())if p.exists()else{'collection_id':coll.id,'collection_slug':slug,'identity':identity,'artifacts':{},'no_native_eval_fabricated':True,'no_training_submitted':True}
for file in [O/'LOCAL_PARENT_SUMMARY.json',R/'EXPERIMENT.md',R/'manifest.json',R/'boundary-audit.json',R/'upload-receipt.json',R/'coverage-plan.json',O/'finish-audit.json']:
 if file.name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(file,collection=slug);receipt['artifacts'][file.name]={'id':a.id,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'state':a.state};p.write_text(json.dumps(receipt,indent=2)+'\n');print(file.name,a.id,a.state,flush=True)
actual=c.artifacts.list(collection_id=coll.id,limit=100);assert{x['id']for x in receipt['artifacts'].values()}<={x.id for x in actual};receipt['verified_collection_membership']=True;p.write_text(json.dumps(receipt,indent=2)+'\n');print('collection_verified',coll.id,flush=True)
