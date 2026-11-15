import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;run=json.loads((R/'run.json').read_text());c=working_client();identity=preflight_identity(c);slug='pokerbench-v4-consistent-knowledge-pilot';coll=c.collections.get_by_slug(slug=slug);file=R/'launch-publication.json';receipt=json.loads(file.read_text())if file.exists()else{'collection_id':coll.id,'train_id':run['train_id'],'identity':identity,'artifacts':{}}
if not receipt.get('native_train_linked'):
 preflight_identity(c);c.collections.add_train_runs(collection_id=coll.id,ids=[run['train_id']]);preflight_identity(c);c.collections.update(collection_id=coll.id,name='PokerBench V4 ad74 knowledge pilot —10 update cap',description='One actual4GPU SFT run train_3c45262ddf1f; oldSFTad74parent,verifiedconsistent-onlydata and LOCAL frozen parent references (not nativeEval/pokerEV).10updates/checkpoints5and10,weights-only,no automatic extension. Sealed final untouched.');receipt['native_train_linked']=True;file.write_text(json.dumps(receipt,indent=2)+'\n')
for p in [R/'README.md',R/'run.json',R/'launch-authorization.json',R/'proposed-ad74-config.json']:
 if p.name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(p,collection=slug);receipt['artifacts'][p.name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};file.write_text(json.dumps(receipt,indent=2)+'\n');print(p.name,a.id,a.state,flush=True)
