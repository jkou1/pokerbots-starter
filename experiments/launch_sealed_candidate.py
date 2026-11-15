"""Launch the one explicitly selected final candidate; no model ranking on this release."""
import argparse,asyncio,json,os,time
from pathlib import Path
from ac2.sdk import Client
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--inference',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--selection-reason',required=True);a=p.parse_args()
root=Path(__file__).resolve().parent.parent/'data/experiments/sealed-final-base20-v1';path=root/'receipt.json';r=json.loads(path.read_text());c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c)
if r.get('candidate',{}).get('eval_id'):
 assert r['candidate']['inference_id']==a.inference and r['candidate']['checkpoint']==a.checkpoint
 print(json.dumps(r['candidate']));raise SystemExit
assert r.get('baseline',{}).get('eval_id') and r['verified_membership']
selected=r.get('selected_candidate')
if selected:assert selected['inference_id']==a.inference and selected['checkpoint']==a.checkpoint
model=c.inference.get(a.inference);assert model.checkpoint_id==a.checkpoint and model.state in ['ready','running','healthy']
opp=c.inference.get(r['frozen_opponent']['inference_id']);assert opp.checkpoint_id==r['frozen_opponent']['checkpoint'] and opp.version==r['frozen_opponent']['version']
assert {x.id for x in c.datasets.active_tasks(r['dataset'])}==set(r['task_ids']) and c.datasets.get(r['dataset']).task_count==6
expected=[json.loads(x) for x in (root/'tasks.jsonl').read_text().splitlines()]
for i,tid in enumerate(r['task_ids']):
 task=c.datasets.load_task(tid);assert task.env_params==expected[i]['env_params'] and task.model_dump(mode='json')['input']==expected[i]['input']
r['selected_candidate']={'inference_id':a.inference,'checkpoint':a.checkpoint,'version':model.version,'selection_reason':a.selection_reason,'selected_at':time.time(),'identity_preflight':identity};path.write_text(json.dumps(r,indent=2)+'\n')
preflight_identity(c);cfg=eval_config(r['dataset'],deployment=a.inference,max_parallel=2);cfg.name='overnight-sealed-final-selected-candidate-vs-base20';cfg.description='One selected candidate, exact same six fresh official30hand deals/seats/frozen opponent as sealed incumbent baseline. No checkpoint ranking on this release. Zero extraGPU.';cfg.max_retries=0
run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r['candidate']={'eval_id':run.eval_id,'inference_id':a.inference,'checkpoint':a.checkpoint,'version':model.version,'submitted_at':time.time(),'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id};r['outcomes_sealed']=False;r['unsealed_reason']='One fixed candidate explicitly selected before querying final outcomes and submitted on the identical frozen release.';path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['candidate']),flush=True)
