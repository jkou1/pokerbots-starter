import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;c=working_client();identity=preflight_identity(c);slug='grpo-checkpoint-decisions-20261115';collection=c.collections.get_by_slug(slug=slug)
p=R/'publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':collection.id,'local_not_native_eval':True,'identity':identity,'artifacts':{}}
for name in ['README.md','summary.json','FRAMEWORK.md']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
