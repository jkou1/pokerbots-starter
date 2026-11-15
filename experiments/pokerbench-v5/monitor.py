"""Actual batch/source/target checkpoint monitor; no extension or deployment."""
import json,sys,os,time,gzip,hashlib,collections,dataclasses,math
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main');from vals_tools.sft_audit import audit_target
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'pete-postflop-v1'));from action_ce import arguments,summarize
from ac2.runtime import Task,compute_content_hash
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
R=Path(__file__).resolve().parent;run=json.loads((R/'run.json').read_text());RUN=run['train_id'];c=working_client();identity=preflight_identity(c);(R/'raw').mkdir(exist_ok=True);os.umask(0o077);mapping={};offset=0;expected={compute_content_hash(Task.model_validate_json(l)):Task.model_validate_json(l)for l in(R/'weighted-train-tasks.jsonl').open()}
while True:
 page=c.datasets.list_tasks('pokerbots-pokerbench-v5-reconciled-pre10x-train',offset=offset,limit=1000)
 for x in page:
  t=expected[x.content_hash];p=t.tags['provenance'];mapping[x.id]={'kind':('preflop'if p['street']=='preflop'else'postflop_reconciled'if'pot_reconciliation'in p else'postflop_consistent'),'sampling_copy':t.env_params.get('sampling_copy'),'target':json.loads(t.input[-1].arguments),'source_provenance':p}
 if len(page)<1000:break
 offset+=len(page)
assert len(mapping)==7369;(R/'task-membership-map.json').write_text(json.dumps(mapping,indent=2)+'\n');statepath=R/'monitor-state.json';old=json.loads(statepath.read_text())if statepath.exists()else{};steps=old.get('managed_steps',{});conversions=old.get('conversions',{})
def save(state):
 p=statepath.with_suffix('.tmp');p.write_text(json.dumps(state,indent=2,default=str)+'\n');p.replace(statepath)
while datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-15T17:00:00+00:00'):
 try:
  info=c.train.get(RUN);metrics=c.train.get_step_metrics(train_job_id=RUN);training=metrics.get('train',[]);checkpoints=list(c.checkpoints.list(train_job_id=RUN));alerts=[]
  for row in training:
   step=int(row['step'])
   if str(step)in steps and steps[str(step)]['samples']==64:continue
   q=c.analytics.query(spec=QuerySpec(source='token_viz',job_ids=[RUN],columns=[ColumnSpec(field=x)for x in ['step','payload','loss']],filters=[FieldFilter(field='step',op='eq',value=step)],limit=128,sort_by='step',sort_order='asc'));unique={}
   for item in q.rows:
    payload=json.loads(item['payload']);unique[payload['sample_index']]=(item,payload)
   if not unique:continue
   assert len(unique)<=64;counts=collections.Counter();copies=collections.Counter();targettokens=collections.Counter();stats=[];errors=[];raw=[]
   for item,payload in unique.values():
    raw.append({**item,'payload':payload});source=mapping.get(payload['datapoint_id'])
    if source is None:errors.append('unknown_remote_task_id');continue
    kind=source['kind'];counts[kind]+=1;copies[str(source['sampling_copy'])]+=1;targettokens[kind]+=sum(x==1 for x in payload['loss_mask'])
    try:
     audit_target(payload);text=''.join(payload['sampled_tokens']);assert text.count('<tool_call>')==1 and text.count('</tool_call>')==1;assert '<function=submit_action>'in text;stats.append(arguments(payload))
    except Exception as e:errors.append(type(e).__name__+':'+str(e))
   f=R/f'raw/managed-step-{step}.jsonl.gz'
   with gzip.open(f,'wt')as out:
    for x in raw:out.write(json.dumps(x)+'\n')
   steps[str(step)]={'samples':len(unique),'expected_batch':64,'full_batch_export':len(unique)==64,'source_kinds':dict(counts),'pre_anchor_sampling_copies':dict(copies),'supervised_tokens_by_kind':dict(targettokens),'boundary_membership_errors':errors,'action_ce':summarize(stats),'raw_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
  errors=[x for s in steps.values()for x in s['boundary_membership_errors']]
  if errors:alerts.append('TARGET/MEMBERSHIPFAIL: preserve failure and coordinate stop, no retry')
  if '0'in steps and steps['0']['full_batch_export']and not{'preflop','postflop_consistent','postflop_reconciled'}<=set(steps['0']['source_kinds']):alerts.append('Firstfull64batchmissingsourcekind;triagesampling')
  for row in training:
   if any(isinstance(row.get(k),float)and not math.isfinite(row[k])for k in ['train/loss','train/grad_norm']):alerts.append('NONFINITE optimizer metric')
  for cp in checkpoints:
   if cp.iter_num not in [9,19]or errors:continue
   state=str(c.checkpoints.promotion_status(cp.id).state);prior=conversions.get(cp.id,{})
   if state in ['missing','none','not_found']and not prior.get('requested'):
    preflight_identity(c);conversions[cp.id]={'iter_num':cp.iter_num,'requested':True,'requested_at':datetime.now(timezone.utc).isoformat()};save({'managed_steps':steps,'conversions':conversions});state=str(c.checkpoints.promote(cp.id).state)
   conversions.setdefault(cp.id,{'iter_num':cp.iter_num});conversions[cp.id]['state']=state
  state={'updated_at':datetime.now(timezone.utc).isoformat(),'monitor_pid':os.getpid(),'train_id':RUN,'job_id':run['job_id'],'status':info.status,'completed':info.completed,'training_updates':len(training),'latest_train_metrics':training[-1]if training else None,'managed_steps':steps,'checkpoints':[dataclasses.asdict(x)for x in checkpoints],'conversions':conversions,'alerts':alerts,'no_extension':True,'no_auto_retry':True,'generation_quality_not_established_by_target_audit':True};save(state);print(state['updated_at'],info.status,'updates',len(training),'audited',len(steps),'checkpoints',len(checkpoints),'alerts',alerts,flush=True)
  if info.completed and all(str(x['step'])in steps for x in training)and all(v.get('state')in ['available','failed','error']for v in conversions.values()):break
 except Exception as e:print(datetime.now(timezone.utc).isoformat(),type(e).__name__,str(e),flush=True)
 time.sleep(30)
