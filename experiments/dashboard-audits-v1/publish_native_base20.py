import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp')
from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent
p=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/native-official30/base-s20/summary.json');d=json.loads(p.read_text())
assert d['completed_logs']==d['planned_games']==6 and d['status']=='succeeded'
d={k:v for k,v in d.items() if k not in ['native_scores','source_manifest']}
d['interpretation']='Native six-game selection, wide CI includes zero; eight invalid decisions block reliability claims. Short cleanup outputs do not establish factual/protocol correctness. Paired incumbent baseline was local, not a second native job. No sealed final queried.'
out=R/'NATIVE_BASE20_OFFICIAL30_SELECTION.json';out.write_text(json.dumps(d,indent=2)+'\n')
c=working_client();preflight_identity(c)
m=c._require_api().request('GET','/eval/eval_b539897717d8').json();assert m['project_id']=='prj_ba36d29befaf' and m['status']=='succeeded'
coll=c.collections.get_by_slug(slug='poker-sft-action-audits-20261115')
preflight_identity(c);c.collections.add_eval_runs(collection_id=coll.id,ids=['eval_b539897717d8'])
preflight_identity(c);a=c.artifacts.upload(out,collection='poker-sft-action-audits-20261115')
receipt={'collection_id':coll.id,'eval_id':'eval_b539897717d8','artifact_id':a.id,'state':a.state,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
assert coll.id in c._require_api().request('GET','/eval/eval_b539897717d8').json()['collection_ids']
(R/'native-base20-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
