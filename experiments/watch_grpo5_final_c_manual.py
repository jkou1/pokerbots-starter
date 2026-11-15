"""Read-only per-game callbacks plus root-approved35/45minute scheduling stop."""
import argparse,json,os,re,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True,choices=['incumbent','grpo5']);a=ap.parse_args();assert a.arm=='incumbent';R=Path('data/experiments/grpo5-fresh-final6-v2')/a.arm;receipt=json.loads((R/'receipt.json').read_text());eid=receipt['eval_id'];original=receipt['submitted_at']+45*60;absolute=original+5*60;c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);preflight_identity(c);p=R/'progress.json';extension_checked=False

def epoch(x):
 d=datetime.fromisoformat(str(x).replace('Z','+00:00'));return(d.replace(tzinfo=timezone.utc)if d.tzinfo is None else d).timestamp()

def progress():
 run=c.eval.get(eid);scores=c.analytics.scores(run_ids=[eid]).to_records();completed={x['agent_trace_id']for x in scores};rows=c.analytics.spans(run_ids=[eid]).select('start_time','end_time','trace_id','input','status','error_message').filter(name='get_completion').to_records();groups={};errors=0
 for row in rows:
  if row.get('error_message')or str(row.get('status')).lower()in['error','failed']:errors+=1
  try:
   items=json.loads(row['input'])if isinstance(row['input'],str)else row['input'];hands=[int(n)for item in items if item.get('role')=='user'for n in re.findall(r'## Hand (\d+) (?:of \d+|is over)',item.get('content',''))];g=groups.setdefault(row['trace_id'],{'max_observed_policy_hand':0,'completion_callbacks':0,'last_successful_callback_at':None});g['max_observed_policy_hand']=max([g['max_observed_policy_hand']]+hands);g['completion_callbacks']+=1
   if row.get('end_time')and not row.get('error_message')and str(row.get('status')).lower()not in['error','failed']:g['last_successful_callback_at']=max(g['last_successful_callback_at']or 0,epoch(row['end_time']))
  except(ValueError,TypeError,AttributeError):errors+=1
 active={k:v for k,v in groups.items()if k not in completed};now=time.time();bad=[x for x in rows if x.get('error_message')or str(x.get('status')).lower()in ['error','failed']];sole_recovered=len(bad)==1 and bad[0].get('error_message')=='Connection error.' and str(bad[0]['start_time']).startswith('2026-11-15T16:09:38') and any(x['trace_id']==bad[0]['trace_id'] and x.get('end_time') and epoch(x['end_time'])>epoch(bad[0]['end_time']) and not x.get('error_message') for x in rows);health=json.load(urllib.request.urlopen('http://localhost:8765/health',timeout=5));healthy=health.get('status')=='ok' and all(x=='ok' for x in health.get('shards',[]));eligible=len(completed)>=4 and len(active)==6-len(completed)and bool(active)and all(v['max_observed_policy_hand']>=20 and v['last_successful_callback_at']and now-v['last_successful_callback_at']<90 for v in active.values())and sole_recovered and healthy
 return{'at':now,'eval_id':eid,'status':run.status,'completed_games':len(completed),'completed_agent_trace_ids':sorted(completed),'policy_game_progress':groups,'unfinished_policy_game_progress':active,'structural_or_parse_errors':errors,'original_deadline':original,'absolute_deadline':absolute,'extension_eligible_at_snapshot':eligible,'scope':'Policycallbackhandobservations only; no rank/EV interpretation; unseen/queuedgame or bustedpolicy withoutfreshcallback cannotproveextensioncondition'}

def save(r):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(r,indent=2)+'\n');q.replace(p)

while True:
 try:r=progress()
 except Exception as exc:
  r={'at':time.time(),'eval_id':eid,'monitor_error':type(exc).__name__+': '+str(exc)[:300],'extension_eligible_at_snapshot':False,'original_deadline':original,'absolute_deadline':absolute}
 save(r);print(json.dumps({k:v for k,v in r.items()if k not in['policy_game_progress','unfinished_policy_game_progress']}),flush=True)
 if r.get('status')in['succeeded','failed','stopped','cancelled']:break
 now=time.time()
 if now>=original and not extension_checked:
  extension_checked=True
  if r.get('extension_eligible_at_snapshot'):
   (R/'manual-runtime-decision.json').write_text(json.dumps(r|{'one_manual_five_minute_allowance_granted':True,'sole_recovered_error_verified':True,'healthy_servers_verified':True},indent=2)+'\n')
  else:
   preflight_identity(c);c.eval.stop(eid);save(r|{'stop_requested_at':time.time(),'stop_reason':'45minuteoriginalwall,no prospectiveextensionproof; supportedSDKnoadmissionpause'});break
 if now>=absolute:
  preflight_identity(c);c.eval.stop(eid);save(r|{'stop_requested_at':time.time(),'stop_reason':'AbsoluteCmanualfive_minute_cap164617UTC,no furtherextension'});break
 time.sleep(min(30,max(0,(absolute if extension_checked else original)-time.time())))
