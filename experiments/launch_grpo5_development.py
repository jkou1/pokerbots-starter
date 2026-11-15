"""Prepare (default) or launch only the coordinator-approved four carried-stack development games."""
import argparse,asyncio,hashlib,json,os,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');p.add_argument('--approval-receipt',type=Path);a=p.parse_args();R=Path('data/experiments/base20-development-v1');source=json.loads((R/'receipt.json').read_text());raw=(R/'tasks.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==source['sha256'];rows=[json.loads(x)for x in raw.splitlines()];assert len(rows)==4 and all(x['env_params']['total_hands']==30 for x in rows)
plan={'candidate':'infer_af5fa217b570','checkpoint':'ckpt_a7a227300baf','version':1,'dataset':source['dataset'],'source_sha256':source['sha256'],'cached_comparisons':{k:source['runs'][k]['eval_id']for k in['incumbent','rl20']},'opponent':source['frozen_opponent'],'games':4,'max_parallel':2,'extra_gpu':0,'root_fullgame_GO_required':True,'final_release_used':False}
if not a.launch:print(json.dumps(plan,indent=2));raise SystemExit
assert a.approval_receipt and json.loads(a.approval_receipt.read_text()).get('root_grpo5_four_development_games_approved')is True
from ac2.sdk import Client
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);m=c.inference.get(plan['candidate']);assert m.checkpoint_id==plan['checkpoint']and m.version==1 and m.state=='ready';opp=c.inference.get(plan['opponent']['inference_id']);assert opp.checkpoint_id==plan['opponent']['checkpoint']and opp.version==1
for k in['incumbent','rl20']:assert c.eval.get(source['runs'][k]['eval_id']).status=='succeeded'
assert c.datasets.get(source['dataset']).task_count==4 and {x.id for x in c.datasets.active_tasks(source['dataset'])}==set(source['task_ids'])
for tid,row in zip(source['task_ids'],rows):
 task=c.datasets.load_task(tid);assert task.input==__import__('ac2.runtime',fromlist=['Task']).Task.model_validate(row).input and task.env_params==row['env_params']
out=Path('data/experiments/base-grpo5-development-v1');out.mkdir(exist_ok=True);receipt=out/'receipt.json';assert not receipt.exists(),'No duplicate fullgames';cfg=eval_config(source['dataset'],deployment=m.id,max_parallel=2);cfg.name='base-standard-grpo5-carried-stack-development4';cfg.description='Existingfour30handdevelopmentdeals vs fixedbase20; comparecachedC/RL20; no finaloutcomeuse,noextraGPU.';cfg.max_retries=0;preflight_identity(c);run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));plan.update(eval_id=run.eval_id,submitted_at=time.time(),identity=identity);receipt.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan))
