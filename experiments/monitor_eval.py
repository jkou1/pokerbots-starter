"""Persist evaluation status and paired score evidence every30seconds."""
import dataclasses,json,time,statistics
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk import Client
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/experiments/evaluation-monitor';OUT.mkdir(parents=True,exist_ok=True)
RUNS={'smoke':'eval_bf31fcaff054','incumbent':'eval_521f73148d31','ad74':'eval_7353b52d4873'}
c=Client(project='vals-hackathon')
while True:
 report={'updated_at':datetime.now(timezone.utc).isoformat(),'runs':{},'official':{}}
 for name,rid in RUNS.items():
  try:
   run=c.eval.get(rid);scores=c.analytics.scores(run_ids=[rid]).to_records();traces=c.analytics.traces(run_ids=[rid]).select('trace_id','status','error','duration_ms','resource_type').to_records()
   report['runs'][name]={'id':rid,'status':run.status,'scores':scores,'traces':traces,'mean_reward':statistics.mean(x['score'] for x in scores) if scores else None}
  except Exception as e:report['runs'][name]={'id':rid,'error':str(e)}
 for name in ['incumbent','ad74']:
  report['official'][name]={'completed':len(list((ROOT/f'data/experiments/overnight-{name}-select/logs').glob('*.json')))}
 tmp=OUT/'status.tmp';tmp.write_text(json.dumps(report,indent=2));tmp.replace(OUT/'status.json')
 brief={'time':report['updated_at'],'runs':{k:{'status':v.get('status'),'scores':len(v.get('scores',[])),'errors':sum(bool(t.get('error')) for t in v.get('traces',[]))} for k,v in report['runs'].items()},'official':report['official']}
 print(json.dumps(brief),flush=True)
 if all(v.get('status') in ('succeeded','failed','stopped','cancelled') for v in report['runs'].values()) and all(v['completed']==12 for v in report['official'].values()):break
 if datetime.now(timezone.utc).timestamp()>1794762000:break
 time.sleep(30)
