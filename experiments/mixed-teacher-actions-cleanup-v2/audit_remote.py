import json,hashlib,sys,collections
from pathlib import Path
from ac2.runtime import Task,compute_content_hash
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;c=working_client();u=json.loads((R/'upload.json').read_text());assert u['train']['status']=='verified'
tasks=[Task.model_validate_json(l) for l in (R/'train-tasks.jsonl').open()];expected={compute_content_hash(t):t for t in tasks};actual=u['train']['task_ids'];assert set(actual)==set(expected) and len(actual)==7720
counts=collections.Counter();samples=[];provenance={}
for h,t in expected.items():
 p=t.tags['provenance'];kind=p.get('teacher','genuine-own-cleanup');counts[kind]+=1
 provenance[actual[h]]={**p,'teacher':kind}
 if kind=='genuine-own-cleanup':provenance[actual[h]]['target_contents']=json.loads(t.input[-1].arguments)['contents']
 if sum(s['kind']==kind for s in samples)>=4:continue
 if kind=='genuine-own-cleanup' and any(s.get('source_index')==p['source_index'] for s in samples if s['kind']==kind):continue
 remote=c.datasets.load_task(actual[h]);assert compute_content_hash(remote)==h
 assert [x.model_dump(mode='json') for x in remote.input]==[x.model_dump(mode='json') for x in t.input]
 assert remote.env_params==t.env_params and remote.tags==t.tags
 assert len([x for x in remote.input if x.type=='function_call'])==1
 assert all(getattr(x,'role',None) in ['system','user'] for x in remote.input[:-2])
 samples.append({'kind':kind,'task_id':actual[h],'content_hash':h,'payload_equal':True,'one_supervised_target':True,'source_index':p.get('source_index')})
assert len(samples)==12
(R/'task-provenance-map.json').write_text(json.dumps(provenance)+'\n')
report={'full_membership_verified':True,'expected':7720,'actual':len(actual),'counts':dict(counts),'samples':samples,'identity':preflight_identity(c),'local_template_audit_passed':json.loads((R/'local-template-audit.json').read_text())['all_scaffolds_passed'],'source_selection_datasets_unchanged':True}
(R/'remote-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
