"""Stop only this approved pilot on confirmed managed source/mask failure; never retry."""
import json,time,sys,math,os
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;run=json.loads((R/'run.json').read_text());c=working_client();out=R/'source-failure-guard.json'
while datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-15T17:00:00+00:00'):
 try:
  state=json.loads((R/'monitor-state.json').read_text());reasons=[]
  for step,d in state.get('managed_steps',{}).items():
   if d['full_batch_export']and d['boundary_membership_errors']:reasons+=d['boundary_membership_errors']
  latest=state.get('latest_train_metrics')or{}
  if any(isinstance(latest.get(k),float)and not math.isfinite(latest[k])for k in ['train/loss','train/grad_norm']):reasons.append('Nonfinite optimizer loss/gradient')
  p=R/'managed-source-target-audit.json'
  if p.exists():
   audit=json.loads(p.read_text())
   for d in audit.get('steps',{}).values():
    if d['observed_sequences']==64:reasons+=d['exact_target_errors']
  record={'updated_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'train_id':run['train_id'],'reasons':reasons,'no_retry_or_extension':True,'stop_requested':False}
  if reasons:
   info=c.train.get(run['train_id'])
   if not info.completed:preflight_identity(c);c.train.stop(run['train_id'],stop_evals=True);record['stop_requested']=True
   out.write_text(json.dumps(record,indent=2)+'\n');print('Confirmed source/mask failure; stop issued if still active',flush=True);break
  out.write_text(json.dumps(record,indent=2)+'\n')
  if state['training_updates']>=20 and len(state.get('managed_steps',{}))>=20:break
 except (OSError,ValueError,KeyError)as e:print(type(e).__name__,str(e),flush=True)
 time.sleep(20)
