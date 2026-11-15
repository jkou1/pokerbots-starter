"""Root-authorized single pilot launch; persisted attempt blocks duplicate retry."""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk.run_config import RunConfig
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;receipt=R/'run.json'
if receipt.exists():raise SystemExit('A launch attempt already exists. Do NOT retry identically; inspect preserved receipt.')
a=json.loads((R/'launch-authorization.json').read_text());assert a['root_GO_received'];u=json.loads((R/'upload-receipt.json').read_text());assert all(u[s]['full_membership_equal']and u[s]['status']=='verified'for s in ['train','select']);config=json.loads((R/'proposed-ad74-config.json').read_text());cfg=RunConfig.from_json(config);assert cfg.model.checkpoint=='ckpt_ad74c826c9ad';s=config['experiment_cfg']['step'];assert s['num_train_steps']==10 and s['checkpoint_interval']==5 and s['problem_batch_size']==64 and s['no_save_optimizer_state']is True and s['keep_last_checkpoints']==2
c=working_client();identity=preflight_identity(c);record={'status':'attempt_locked','created_at':datetime.now(timezone.utc).isoformat(),'identity':identity,'config':config,'authorization':a,'requested_gpus':{'train':4,'rollout':0,'eval':0},'no_identical_retry':True,'hashes':{f:hashlib.sha256((R/f).read_bytes()).hexdigest()for f in ['original-prepared-ad74-config.json','proposed-ad74-config.json','manifest.json','boundary-audit.json','upload-receipt.json','EXPERIMENT.md']}};receipt.write_text(json.dumps(record,indent=2)+'\n');preflight_identity(c)
try:
 result=c.train.run(cfg);record.update(status='submitted',train_id=result.train_id);receipt.write_text(json.dumps(record,indent=2)+'\n');info=c.train.get(result.train_id);job=c.jobs.get(info.job_id);assert job.owner_email=='lmathias@berkeley.edu'and job.unix_uid==10464;record.update(status=info.status,job_id=info.job_id,actual_owner=job.owner_email,actual_unix_uid=job.unix_uid);receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k]for k in ['status','train_id','job_id','actual_owner','actual_unix_uid','requested_gpus']},indent=2))
except Exception as e:
 record['submission_error']=type(e).__name__+':'+str(e);receipt.write_text(json.dumps(record,indent=2)+'\n');raise
