import json,time,os,argparse
from pathlib import Path
from ac2.sdk import Client
from datetime import datetime,timezone
from pokerbots_working_client import preflight_identity
args=argparse.ArgumentParser();args.add_argument('--eval',required=True);args.add_argument('--submitted-at',type=float,required=True);args.add_argument('--label',required=True);a=args.parse_args();c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);eid=a.eval;deadline=a.submitted_at+900;p=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/late-grpo-fresh64-v1')/(a.label+'-deadline.json')
while time.time()<deadline:
 r=c.eval.get(eid);record={'eval_id':eid,'last_status':r.status,'checked_at':time.time(),'deadline':deadline};p.write_text(json.dumps(record,indent=2)+'\n')
 if r.status in ['succeeded','failed','stopped','cancelled']:print('terminal',r.status,flush=True);raise SystemExit
 time.sleep(min(30,max(0,deadline-time.time())))
r=c.eval.get(eid)
if r.status in ['succeeded','failed','stopped','cancelled']:record.update(terminal_status=r.status,terminal_at=time.time());p.write_text(json.dumps(record,indent=2)+'\n');print('terminal',r.status,flush=True);raise SystemExit
scores=c.analytics.scores(run_ids=[eid]).to_records();spans=c.analytics.spans(run_ids=[eid]).select('start_time','end_time','status','error_message').filter(name='grade').to_records();good=[x for x in spans if not x.get('error_message')and str(x.get('status','')).lower()not in['error','failed']];times=[datetime.fromisoformat(str(x.get('end_time')or x.get('start_time'))).replace(tzinfo=timezone.utc).timestamp()for x in good];age=time.time()-max(times)if times else None;bad=[x for x in spans if x.get('error_message')or str(x.get('status','')).lower()in['error','failed']];extend=len(scores)>=48 and age is not None and age<60 and not bad;record.update(graded_at_original_wall=len(scores),latest_successful_grade_age=age,structural_grade_errors=len(bad),extension_criteria_pass=extend,absolute_deadline=deadline+180);p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
if extend:
 while time.time()<deadline+180:
  r=c.eval.get(eid)
  if r.status in ['succeeded','failed','stopped','cancelled']:record.update(terminal_status=r.status,terminal_at=time.time());p.write_text(json.dumps(record,indent=2)+'\n');print('terminal',r.status,flush=True);raise SystemExit
  time.sleep(min(10,max(0,deadline+180-time.time())))
preflight_identity(c);c.eval.stop(eid);record.update(stop_requested_at=time.time(),stop_reason='Prospective15minute/conditional18minuteabsolute hardwall');p.write_text(json.dumps(record,indent=2)+'\n');print('harddeadline_stoprequested',flush=True)
