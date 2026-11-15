"""Launch a resumable native32hand screen on an existing served checkpoint, no new GPUs."""
import argparse,asyncio,hashlib,json,os,time
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--inference',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--iteration',type=int,required=True);p.add_argument('--label',required=True);a=p.parse_args();root=Path(__file__).resolve().parent.parent/'data/experiments';out=root/'rl-checkpoint-selection'/a.label;out.mkdir(parents=True,exist_ok=True);receipt=out/'native-run.json'
if receipt.exists():
 r=json.loads(receipt.read_text());assert r['checkpoint']==a.checkpoint and r['model']==a.model;print(json.dumps(r));raise SystemExit
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);source=json.loads((root/'fast-screen-v1/receipt.json').read_text());raw=(root/'fast-screen-v1/tasks.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==source['sha256'];name='pokerbots-overnight-fast-select-v1';assert {r.id for r in c.datasets.active_tasks(name)}==set(source['task_ids'])
tasks=[Task.model_validate(json.loads(line)) for line in raw.splitlines()]
for index in [0,16,31]:
 loaded=c.datasets.load_task(source['task_ids'][index]);assert loaded.input==tasks[index].input and loaded.env_params==tasks[index].env_params
preflight_identity(c);config=eval_config(name,deployment=a.model,max_parallel=2);config.name=f'overnight-grpo-step{a.iteration}-paired32-select';config.description='Fixed32deals,seats,opponents vs cachedparent eval7353. Existingdeployment0extraGPU; compareunclippedgraderEV andinvalidrate, notclippedreward.';config.max_retries=0;run=asyncio.run(c.eval.run(config,project_version_id='pver_3b0aae1bdaea'));r={'eval_id':run.eval_id,'name':config.name,'checkpoint':a.checkpoint,'iteration':a.iteration,'inference_id':a.inference,'model':a.model,'parent_eval_id':'eval_7353b52d4873','parent_checkpoint':'ckpt_ad74c826c9ad','dataset':name,'dataset_sha256':source['sha256'],'verified_membership':True,'verified_content_indices':[0,16,31],'identity_preflight':identity,'created_at':time.time(),'gpu_allocation_extra':0,'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id};receipt.write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
