import json,sys,hashlib
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval')
from vals_tools.pete_eval import imitation_metrics
R=Path(__file__).resolve().parent;S=Path('/Users/lance/Documents/pokerbots-pokerbench/experiments/mixed-teacher-actions-v1/fast-select.jsonl');E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/mixed-teacher-select')
rows=[json.loads(l) for l in S.open()];report={'scope':'LOCAL fixedSELECT imitation only, not poker EV or placement','records':256,'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'models':{}}
assert len(rows)==256 and all(r['split']=='select' for r in rows)
for name in ['incumbent','rl20']:
 d=json.loads((E/f'{name}.json').read_text());assert d['status']=='complete' and len(d['results'])==256
 assert all(r['provenance']==p['provenance'] for r,p in zip(rows,d['results']))
 groups=defaultdict(list)
 for i,r in enumerate(rows):
  for k in [('teacher',r['provenance']['teacher']),('street',r['provenance']['street']),('teacher_street',r['provenance']['teacher']+':'+r['provenance']['street'])]:groups[k].append(i)
 metrics={}
 for (kind,key),indices in groups.items():metrics.setdefault(kind,{})[key]=imitation_metrics([rows[i] for i in indices],[d['results'][i]['action'] for i in indices])
 metrics['all']=imitation_metrics(rows,[r['action'] for r in d['results']])
 for kind in ['teacher','street','teacher_street']:
  metrics[f'{kind}_balanced_agreement']=sum(x['action_accuracy'] for x in metrics[kind].values())/len(metrics[kind])
 aggressive=[i for i,r in enumerate(rows) if r['target']['action'] in ['bet','raise']]
 metrics['exact_sizing_against_all_teacher_bets_raises']={'examples':len(aggressive),'hits':sum(d['results'][i]['action'].get('action')==rows[i]['target']['action'] and d['results'][i]['action'].get('amount')==rows[i]['target']['amount'] for i in aggressive)}
 metrics['source_results_sha256']=hashlib.sha256((E/f'{name}.json').read_bytes()).hexdigest();report['models'][name]=metrics
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({n:{k:v for k,v in m.items() if k not in ['teacher','street','teacher_street']} for n,m in report['models'].items()},indent=2))
