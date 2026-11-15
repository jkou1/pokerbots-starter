"""Submit the ONE coordinator-approved queued mixed-teacher base pilot."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from ac2.sdk.run_config import RunConfig
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
ROOT=Path(__file__).resolve().parent
receipt=ROOT/'run.json'
if receipt.exists() and json.loads(receipt.read_text()).get('train_id'):raise SystemExit('Already submitted; refuse a second mixed-teacher run')
upload=json.loads((ROOT/'upload.json').read_text());assert all(upload[s]['status']=='verified' for s in ['train','select','eval','fast-select'])
audit=json.loads((ROOT/'remote-scaffold-audit.json').read_text());assert len(audit['samples'])==12 and audit['full_membership_verified']
config=json.loads((ROOT/'proposed-config.json').read_text());assert config['model']=='Qwen/Qwen3.6-35B-A3B' and not config.get('from_checkpoint');assert config['experiment_cfg']['step']['num_train_steps']==10 and config['experiment_cfg']['step']['checkpoint_interval']==5
policy=json.loads((ROOT/'STOP_AND_EXTENSION_POLICY.json').read_text());assert policy['initial_max_updates']==10 and not policy['automatic_extension']
c=working_client();identity=preflight_identity(c)
manifest={'status':'prepared','identity':identity,'config':config,'requested_training_gpus':4,'requested_rollout_gpus':0,'requested_eval_gpus':0,'initial_max_updates':10,'no_automatic_extension':True,'coordinator_authorization':'One queued BASE mixedPeteCarlos pilot; do not interrupt currentGRPO.','created_at':datetime.now(timezone.utc).isoformat(),'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['quality.json','upload.json','remote-scaffold-audit.json','prefix-teacher-balance.json','STOP_AND_EXTENSION_POLICY.json','EXPERIMENT.md']}}
receipt.write_text(json.dumps(manifest,indent=2)+'\n');preflight_identity(c);result=c.train.run(RunConfig.from_json(config));manifest.update(status='submitted',train_id=result.train_id);receipt.write_text(json.dumps(manifest,indent=2)+'\n')
info=c.train.get(result.train_id);job=c.jobs.get(info.job_id);assert job.owner_email=='lmathias@berkeley.edu' and job.unix_uid==10464
manifest.update(status=info.status,job_id=info.job_id,actual_owner=job.owner_email,actual_unix_uid=job.unix_uid);receipt.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'train_id':result.train_id,'job_id':info.job_id,'status':info.status,'owner':job.owner_email,'unix_uid':job.unix_uid,'gpus':4,'updates':10,'batch':128,'checkpoint_iterations':[4,9]},indent=2))
