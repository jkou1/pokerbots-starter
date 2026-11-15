"""Durable target/teacher/milestone monitor for the one approved10-update pilot.

No extension/deployment is performed. It may stop only this own pilot for a
sustained setup failure/nonfinite training metric; natural10-step cap is fixed.
"""
import collections,dataclasses,gzip,hashlib,json,math,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,'/tmp')
from pokerbots_working_client import working_client,preflight_identity
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.sft_audit import audit_target
sys.path.insert(0,'/Users/lance/Documents/pokerbots-pokerbench/experiments/pete-postflop-v1')
from action_ce import arguments,summarize
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
ROOT=Path(__file__).resolve().parent
run=json.loads((ROOT/'run.json').read_text());RUN=run['train_id'];c=working_client();identity=preflight_identity(c)
provenance=json.loads((ROOT/'task-provenance-map.json').read_text());p=ROOT/'monitor-state.json';old=json.loads(p.read_text()) if p.exists() else {};steps=old.get('managed_steps',{});conversions=old.get('conversions',{});bad_polls=old.get('bad_audit_polls',0);repair_stopped=old.get('repair_stop_requested',False)
def save(value):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,default=str)+'\n');temp.replace(p)
while datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-15T17:00:00+00:00'):
 sleep_seconds=60
 try:
  info=c.train.get(RUN);metrics=c.train.get_step_metrics(train_job_id=RUN);training=metrics.get('train',[]);sleep_seconds=60 if info.status in ['pending','queued'] else 30;checkpoints=list(c.checkpoints.list(train_job_id=RUN));alerts=[];reasons=[]
  for row in training:
   step=int(row['step'])
   if str(step) in steps and (steps[str(step)]['samples']>=128 or steps[str(step)].get('stable_export_polls',0)>=2):continue
   result=c.analytics.query(spec=QuerySpec(source='token_viz',job_ids=[RUN],columns=[ColumnSpec(field=x) for x in ['step','payload','loss']],filters=[FieldFilter(field='step',op='eq',value=step)],sort_by='step',sort_order='asc',limit=256))
   unique={}
   for item in result.rows:
    payload=json.loads(item['payload']);unique[payload['sample_index']]=(item,payload)
   if not unique:continue
   if len(unique)>128:raise ValueError(f'More managed sequences than configured128 batch: step{step},found{len(unique)}')
   prior=steps.get(str(step),{});stable=prior.get('stable_export_polls',0)+1 if prior.get('samples')==len(unique) else 0
   counts=collections.Counter();stats=[];errors=[];raw=[]
   for item,payload in unique.values():
    raw.append({**item,'payload':payload});ident=payload['datapoint_id'];source=provenance.get(ident)
    if source is None:errors.append(f'unknown_task_id:{ident}')
    else:counts[source['teacher']]+=1
    if any(t in payload['student_prompt'] for t in ['house-professor-pete','house-chatty-carlos']):errors.append('Teacher identity leaked into student prompt')
    try:audit_target(payload);stats.append(arguments(payload))
    except Exception as e:errors.append(f'{type(e).__name__}:{e}')
   with gzip.open(ROOT/f'managed-step-{step}.jsonl.gz','wt') as f:
    for rowdata in raw:f.write(json.dumps(rowdata)+'\n')
   steps[str(step)]={'samples':len(unique),'expected_optimizer_batch':128,'export_full_batch':len(unique)==128,'stable_export_polls':stable,'teachers':dict(counts),'errors':errors,'action_ce':summarize(stats),'raw_sha256':hashlib.sha256((ROOT/f'managed-step-{step}.jsonl.gz').read_bytes()).hexdigest()}
  audit_errors=[e for s in steps.values() for e in s['errors']]
  bad_polls=bad_polls+1 if audit_errors else 0
  if bad_polls>=2:reasons.append('Managed boundary or task-membership audit failure persisted for two polls')
  if '0' in steps and '1' in steps:
   seen=set(steps['0']['teachers'])|set(steps['1']['teachers'])
   if seen!={'house-professor-pete','house-chatty-carlos'}:
    if steps['0']['export_full_batch'] and steps['1']['export_full_batch']:reasons.append('First two complete managed batches do not contain both teachers')
    else:alerts.append('Both teachers not yet confirmed in sampled token visualization; partial export cannot establish full-batch absence')
  for row in training:
   if any(isinstance(row.get(k),float) and not math.isfinite(row[k]) for k in ['train/loss','train/grad_norm']):reasons.append('Nonfinite optimizer loss or gradient')
  if len(training)>10:reasons.append('Approved10-update cap exceeded')
  if info.dataset_names and info.dataset_names!=['pokerbots-mixed-pete-carlos-actions-v1-train']:reasons.append('Unexpected training dataset')
  for ckpt in checkpoints:
   if ckpt.iter_num not in [4,9] or audit_errors:continue
   state=str(c.checkpoints.promotion_status(ckpt.id).state);prior=conversions.get(ckpt.id,{})
   if state in ['missing','none','not_found'] and not prior.get('requested'):
    preflight_identity(c);conversions[ckpt.id]={'iter_num':ckpt.iter_num,'requested':True,'identity':identity,'requested_at':datetime.now(timezone.utc).isoformat()};save({'managed_steps':steps,'conversions':conversions});state=str(c.checkpoints.promote(ckpt.id).state)
   conversions.setdefault(ckpt.id,{'iter_num':ckpt.iter_num});conversions[ckpt.id]['state']=state
  if any(not x.get('export_full_batch',True) for x in steps.values()):alerts.append('Token visualization may export only a sample of each128sequence batch; action CE/teacher counts are labeled by observed coverage')
  if checkpoints:alerts.append('Checkpoint ready: run fixed balanced256, legacy147/354 retention and official poker diagnostics before any extension')
  if len(training)>=10:alerts.append('Initial10updates consumed; no automatic extension is authorized')
  state={'updated_at':datetime.now(timezone.utc).isoformat(),'monitor_pid':os.getpid(),'run':RUN,'train_status':info.status,'completed':info.completed,'identity':identity,'training_updates':len(training),'latest_train_metrics':training[-1] if training else None,'checkpoints':[dataclasses.asdict(x) for x in checkpoints],'managed_steps':steps,'conversions':conversions,'bad_audit_polls':bad_polls,'repair_stop_requested':repair_stopped,'repair_reasons':reasons,'alerts':alerts,'no_automatic_extension':True,'student_generated_legality':'not measured by target-token audit; requires separate real inference evaluation'}
  if reasons and not repair_stopped and not info.completed:
   preflight_identity(c);c.train.stop(RUN,stop_evals=True);repair_stopped=True;state['repair_stop_requested']=True
  save(state);print(state['updated_at'],info.status,'updates',len(training),'audited_steps',len(steps),'checkpoints',len(checkpoints),'repair',reasons,flush=True)
  if info.completed and all(str(row['step']) in steps for row in training) and all(v.get('state') in ['available','ready','succeeded','completed','converted','failed','error'] for v in conversions.values()):break
 except Exception as e:print(datetime.now(timezone.utc).isoformat(),type(e).__name__,str(e),flush=True)
 time.sleep(sleep_seconds)
