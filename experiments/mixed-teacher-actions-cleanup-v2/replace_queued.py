"""One authorized protocol-bugfix replacement, only while old job is pending."""
import json,sys,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk.run_config import RunConfig
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;A=R.parent/'mixed-teacher-actions-v1';OLD='train_93e592d258f9';receipt=R/'run.json'
if receipt.exists() and json.loads(receipt.read_text()).get('train_id'):raise SystemExit('Replacement already submitted; no second mixed control')
audit=json.loads((R/'remote-audit.json').read_text());assert audit['full_membership_verified'] and len(audit['samples'])==12
local=json.loads((R/'local-template-audit.json').read_text());assert local['records']==7720 and local['all_scaffolds_passed']
cfg=json.loads((R/'proposed-config.json').read_text());validated=RunConfig.from_json(cfg)
assert cfg['model']=='Qwen/Qwen3.6-35B-A3B' and not cfg.get('from_checkpoint')
s=cfg['experiment_cfg']['step'];assert s['num_train_steps']==10 and s['problem_batch_size']==128 and s['checkpoint_interval']==5
assert cfg['experiment_cfg']['rollout']['n_inference_replicas']==0 and cfg['experiment_cfg']['eval']['mode']=='off'
c=working_client();identity=preflight_identity(c)
oldinfo=c.train.get(OLD);metrics=c.train.get_step_metrics(train_job_id=OLD);oldjob=c.jobs.get(oldinfo.job_id)
precheck={'train_status':oldinfo.status,'job_state':oldjob.state,'optimizer_updates':len(metrics.get('train',[])),'checked_at':datetime.now(timezone.utc).isoformat()}
manifest={'identity':identity,'config':cfg,'replaces':OLD,'old_job_id':oldinfo.job_id,'reason':'ObservedincorrectcleanuptoolroutinginbaseSFT;protocolretentionbugfix,notidentitymigration','old_config_preserved_at':str(A/'run.json'),'old_pre_action_check':precheck,'requested_training_gpus':4,'requested_rollout_gpus':0,'requested_eval_gpus':0,'initial_max_updates':10,'no_automatic_extension':True,'created_at':datetime.now(timezone.utc).isoformat()}
receipt.write_text(json.dumps(manifest,indent=2)+'\n')
if oldinfo.status not in ['pending','queued'] or str(oldjob.state).lower() not in ['pending','queued'] or precheck['optimizer_updates']:
 manifest['status']='not_replaced_old_started';receipt.write_text(json.dumps(manifest,indent=2)+'\n');raise SystemExit('Oldjobstarted or state uncertain; left configuration fixed')
# Recheck immediately before authorized cancellation; refuse any running status even with zero updates.
preflight_identity(c);latest=c.train.get(OLD);job=c.jobs.get(latest.job_id);nowmetrics=c.train.get_step_metrics(train_job_id=OLD)
if latest.status not in ['pending','queued'] or str(job.state).lower() not in ['pending','queued'] or nowmetrics.get('train',[]):raise SystemExit('Oldjob state changed; do not cancel running job')
c.train.stop(OLD,stop_evals=True);manifest['old_queued_stop_requested_at']=datetime.now(timezone.utc).isoformat();receipt.write_text(json.dumps(manifest,indent=2)+'\n')
for _ in range(20):
 stopped=c.train.get(OLD);sj=c.jobs.get(stopped.job_id)
 if stopped.completed or str(sj.state).lower() in ['stopped','cancelled','canceled','failed','completed','succeeded']:break
 time.sleep(2)
else:raise RuntimeError('Oldqueuedjob stop not confirmed; no replacement submitted')
manifest['old_stop_verified']={'train_status':stopped.status,'job_state':sj.state};receipt.write_text(json.dumps(manifest,indent=2)+'\n')
preflight_identity(c);result=c.train.run(validated);manifest.update(train_id=result.train_id,status='submitted');receipt.write_text(json.dumps(manifest,indent=2)+'\n')
info=c.train.get(result.train_id);job=c.jobs.get(info.job_id);assert job.owner_email=='lmathias@berkeley.edu' and job.unix_uid==10464
manifest.update(job_id=info.job_id,status=info.status,actual_owner=job.owner_email,actual_unix_uid=job.unix_uid);receipt.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
