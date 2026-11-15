"""Read-only native eval monitor through09:00PST; terminal results are cached."""
import json,os,time
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
ROOT=Path(__file__).resolve().parent.parent/'data/experiments';OUT=ROOT/'native-evaluation-monitor';OUT.mkdir(exist_ok=True);c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);cache={}
while time.time()<1794762000:
 tracked={}
 for p in (ROOT/'rl-checkpoint-selection').glob('*/native-run.json'):
  r=json.loads(p.read_text());tracked[r['eval_id']]={'label':p.parent.name,'expected':32,'kind':'checkpoint_screen'}
 for p in (ROOT/'candidate-serving-audit').glob('*native-smoke.json'):
  r=json.loads(p.read_text());tracked[r['eval_id']]={'label':p.stem,'expected':4,'kind':'smoke'}
 for p in (ROOT/'platform-official30-v1').glob('*/receipt.json'):
  r=json.loads(p.read_text())
  for label,e in r.get('evaluations',{}).items():tracked[e['eval_id']]={'label':label+'-'+p.parent.name,'expected':6,'kind':'official30'}
 dev=ROOT/'base20-development-v1/receipt.json'
 if dev.exists():
  for label,r in json.loads(dev.read_text()).get('runs',{}).items():tracked[r['eval_id']]={'label':'dev4-'+label,'expected':4,'kind':'development30'}
 sealed=ROOT/'sealed-final-base20-v1/receipt.json'
 if sealed.exists():
  r=json.loads(sealed.read_text())
  if r.get('baseline',{}).get('eval_id'):tracked[r['baseline']['eval_id']]={'label':'sealed-final-baseline-health-only','expected':6,'kind':'sealed_health_only'}
 report={'updated_at':datetime.now(timezone.utc).isoformat(),'read_identity':identity,'runs':{}}
 for rid,meta in tracked.items():
  if rid in cache:report['runs'][rid]=cache[rid];continue
  try:
   run=c.eval.get(rid);scores=[] if meta['kind']=='sealed_health_only' else c.analytics.scores(run_ids=[rid]).to_records();row=meta|{'status':run.status,'compute_job':run.job_id,'graded':len(scores),'scores':scores};report['runs'][rid]=row
   if run.status in ['failed','stopped','cancelled'] or (run.status=='succeeded' and (meta['kind']=='sealed_health_only' or len(scores)>=meta['expected'])):cache[rid]=row
  except Exception as e:report['runs'][rid]=meta|{'query_error':type(e).__name__+': '+str(e)[:300]}
 report['local_completed_games']={name:len(list((ROOT/name/'logs').glob('*.json'))) for name in ['overnight-incumbent-select','overnight-ad74-select','overnight-incumbent-frozen-select']};tmp=OUT/'status.tmp';tmp.write_text(json.dumps(report,indent=2));tmp.replace(OUT/'status.json');print(json.dumps({'time':report['updated_at'],'runs':{v['label']:{'status':v.get('status'),'graded':v.get('graded'),'expected':v['expected'],'error':v.get('query_error')} for v in report['runs'].values()},'local':report['local_completed_games']}),flush=True);time.sleep(60)
