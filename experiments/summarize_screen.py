import json,re,statistics,random
from pathlib import Path
from ac2.sdk import Client
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/fast-screen-v1';c=Client(project='vals-hackathon');rec=json.loads((ROOT/'receipt.json').read_text());runs={}
for model,rid in rec['models'].items():
 rows=c.analytics.scores(run_ids=[rid]).to_records();vals={}
 for r in rows:
  text=r.get('reasoning','');m=re.search(r'EV ([+-]?[\d.]+) BB',text);f=re.search(r'(\d+) format errors',text)
  vals[r['datapoint_id']]={'reward':r['score'],'ev_bb':float(m.group(1)) if m else None,'format_errors':int(f.group(1)) if f else None,'reasoning':text}
 runs[model]={'eval_id':rid,'status':c.eval.get(rid).status,'tasks':vals,'mean_reward':statistics.mean(v['reward'] for v in vals.values()) if vals else None,'mean_ev_bb':statistics.mean(v['ev_bb'] for v in vals.values() if v['ev_bb'] is not None) if vals else None,'format_errors':sum(v['format_errors'] or 0 for v in vals.values())}
models=list(runs);common=set(runs[models[0]]['tasks'])&set(runs[models[1]]['tasks']);diffs=[runs[models[0]]['tasks'][k]['ev_bb']-runs[models[1]]['tasks'][k]['ev_bb'] for k in sorted(common)];rng=random.Random(42);b=sorted(statistics.mean(rng.choices(diffs,k=len(diffs))) for _ in range(2000)) if diffs else []
out={'runs':runs,'paired':{'tasks':len(common),'incumbent_minus_ad74_mean_ev_bb':statistics.mean(diffs) if diffs else None,'bootstrap_ci95':[b[50],b[1950]] if b else None},'scope':'single-hand selection against frozen checkpoint; not full-game placement'};(ROOT/'summary.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v if k!='runs' else {m:{k:v for k,v in r.items() if k!='tasks'} for m,r in v.items()} for k,v in out.items()},indent=2))
