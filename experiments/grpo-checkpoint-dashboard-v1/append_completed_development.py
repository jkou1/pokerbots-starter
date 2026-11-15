import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments');c=working_client();identity=preflight_identity(c);slug='grpo-checkpoint-decisions-20261115';coll=c.collections.get_by_slug(slug=slug)
d=json.loads((E/'base20-development-v1/summary.json').read_text());assert d['matched_games']==4
for name,r in d['runs'].items():
 assert r['status']=='succeeded' and r['completed_games']==r['planned_games']==4
 d['runs'][name]={k:v for k,v in r.items() if k not in ['games','source_manifest']}
f=json.loads((E/'fullschema-functional30/rl20/summary.json').read_text());assert f['status']=='succeeded' and f['hands']==30
f.pop('source',None)
(R/'COMPLETED_DEVELOPMENT_SELECTION.json').write_text(json.dumps(d,indent=2)+'\n');(R/'FUNCTIONAL_LOCAL_DEFAULT_SCHEMA.json').write_text(json.dumps(f,indent=2)+'\n')
for ident in ['eval_0d1639973dff','eval_41013908bd59','eval_79f6e2df2956']:
 m=c._require_api().request('GET',f'/eval/{ident}').json();assert m['status']=='succeeded' and m['project_id']=='prj_ba36d29befaf'
preflight_identity(c);c.collections.add_eval_runs(collection_id=coll.id,ids=['eval_79f6e2df2956'])
(R/'COMPLETED_DEVELOPMENT_README.md').write_text('''# Completed RL20 development selection and functional evidence

Supersedes the earlier PENDING development snapshot; both paired native jobs completed4/4 games. RL20 mean placement3 versus incumbent4; paired placement improvement+1 with95%bootstrapCI[-0.5,+2.5]. Paired unclipped EV gain+55.77425BB/game withCI[-11.6425,+110.215]. These small-sample intervals include zero; directional evidence is not proven superiority. Raw EV uses the official adjustment, with unsupported sidepots falling back to realized return. Clipped dashboard reward is not placement or poker EV.

RL20:0invalid/217policy decisions,0busts,120/120 exact accepted cleanup updates,0wrong-tool/retry/cut/unchanged. Incumbent:2invalid/154decisions,2busts,14cleanup cuts. Cleanup protocol acceptance does not establish factual memory quality.

A separate single30hand native functional smoke, eval_79f6e2df2956, passed the LOCAL-default optional schema(action/amount/p_win/read/say):0invalid/53decisions,30/30accepted cleanup updates,0wrong-tool/retry/cut/unchanged,talkempty. This is functional-only evidence, not another performance ranking. Actual Arena tool definitions were not independently retrieved; do not infer Arena p_win/read requirements.

No sealed-final outcomes were queried for this publication. Final results remain outside this selection evidence.
''')
p=R/'completed-development-publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'identity':identity,'artifacts':{}}
for name in ['COMPLETED_DEVELOPMENT_README.md','COMPLETED_DEVELOPMENT_SELECTION.json','FUNCTIONAL_LOCAL_DEFAULT_SCHEMA.json']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
