"""Wait for authorized window end; fresh read-only dependency/routing proof, no deletion."""
import argparse,hashlib,json,os,subprocess,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--wait',action='store_true');a=p.parse_args();deadline=1794762000
while time.time()<deadline:
 if not a.wait:raise SystemExit('Before17:00UTC; no check/deletion')
 time.sleep(min(30,deadline-time.time()))
R=Path('data/experiments');out=R/'rl20-fallback-window-end';out.mkdir(exist_ok=True);c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);now=datetime.now(timezone.utc);cutoff=now-timedelta(minutes=15);sources={};proof={};amb=[]
for label,iid in [('C','infer_b0f5e9429b7e'),('fallback','infer_c4c38820538f')]:
 q=QuerySpec(source='spans',projects=['vals-hackathon'],job_ids=[iid],columns=[ColumnSpec(field=x)for x in ['start_time','end_time','span_id','attributes','status','error_message']],filters=[FieldFilter(field='name',op='eq',value='inference.request'),FieldFilter(field='start_time',op='ge',value=cutoff.isoformat())],limit=250,sort_by='start_time',sort_order='desc');rows=c.analytics.query(spec=q).rows;raw=json.dumps(rows,default=str).encode();(out/(label+'-private-spans.json')).write_bytes(raw);sources[label]={'rows':len(rows),'sha256':hashlib.sha256(raw).hexdigest()};arena=[]
 for row in rows:
  attrs=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];ids=[x for x in attrs.values()if isinstance(x,str)and x.startswith('vals-arena/')]
  if ids:arena.append({'start':row['start_time'],'end':row.get('end_time'),'span_id':row['span_id']})
 proof[label]={'actual_arena':arena,'inflight_requests':sum(not x.get('end_time')for x in rows)}
 if len(rows)==250 and label=='fallback':amb.append('fallbackquerysaturated')
active=[]
for status in ['running','pending','queued','created','starting']:
 page=c.eval.list(status=status,limit=100);active.extend({'eval_id':x.id,'status':x.status,'inference':x.inference_deployment_id}for x in page)
 if len(page)==100:amb.append('activeevalpage_saturated_'+status)
argv=subprocess.check_output(['ps','-axo','pid=,command='],text=True);local=[]
for line in argv.splitlines():
 if any(x in line for x in ['run_rl20_fallback_functional.py','rl20-fallback-serving.json','infer_c4c38820538f']):local.append(line.strip().split(None,1)[0])
# ps text is inspected only in memory; no argv/env/secrets are saved.
if active:amb.append('active_native_evals')
if local:amb.append('local_fallback_dependency')
if not proof['C']['actual_arena']:amb.append('no_fresh_positive_C_arena_route')
if proof['fallback']['actual_arena']:amb.append('fallback_actual_Arena_use')
if proof['fallback']['inflight_requests']:amb.append('fallback_inflight_requests')
m=c.inference.get('infer_c4c38820538f');assert m.checkpoint_id=='ckpt_11e7c430069c' and m.version==1 and m.deployment.id=='dep_5d643bed4968';assert c.checkpoints.promotion_status(m.checkpoint_id).state=='available'
for iid in ['infer_b0f5e9429b7e','infer_af82066205bf','infer_21f395f49bff']:assert c.inference.get(iid).state=='ready'
r={'at':time.time(),'identity':identity,'cutoff_utc':cutoff.isoformat(),'source_hashes':sources,'route_proof':proof,'active_native_evals':active,'local_dependency_pids':local,'ambiguities':amb,'eligible_for_exact_root_authorized_retirement':not amb,'inference_id':m.id,'dispatch_id':m.deployment.id,'checkpoint':m.checkpoint_id,'no_deletion_by_checker':True};(out/'dependency-proof.json').write_text(json.dumps(r,indent=2,default=str)+'\n');print(json.dumps(r,indent=2,default=str),flush=True)
