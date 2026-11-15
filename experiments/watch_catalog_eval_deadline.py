import json,os,time
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);path=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/late-grpo-fresh64-v1/catalog-base-deadline.json');first=1794748802;last=1794748980;eid='eval_3af9891def09'
while time.time()<first:time.sleep(min(10,first-time.time()))
run=c.eval.get(eid);scores=c.analytics.scores(run_ids=[eid]).to_records();spans=c.analytics.spans(run_ids=[eid]).select('start_time','end_time').filter(name='grade').to_records();ends=[datetime.fromisoformat(str(s.get('end_time')or s.get('start_time'))).replace(tzinfo=timezone.utc).timestamp()for s in spans];age=time.time()-max(ends)if ends else None;extend=run.status=='running'and len(scores)>=48 and age is not None and age<60;r={'eval_id':eid,'checked_at':time.time(),'status':run.status,'graded':len(scores),'latest_grade_age_seconds':age,'extension_criteria_pass':extend,'final_deadline':last};path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
if run.status in ['succeeded','failed','stopped','cancelled']:raise SystemExit
if extend:
 while time.time()<last:
  run=c.eval.get(eid)
  if run.status in ['succeeded','failed','stopped','cancelled']:r.update(terminal_status=run.status,terminal_at=time.time());path.write_text(json.dumps(r,indent=2)+'\n');print('terminal',run.status,flush=True);raise SystemExit
  time.sleep(min(10,last-time.time()))
preflight_identity(c);c.eval.stop(eid);r.update(stop_requested_at=time.time(),stop_reason='Hard deadline or no conditionalextension; supportedAPI has no admissionpause');path.write_text(json.dumps(r,indent=2)+'\n');print('STOP_REQUESTED',flush=True)
