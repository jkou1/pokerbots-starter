"""Root-released fresh6 FINAL: immutable parent5 versus C, no child selection."""
import argparse,asyncio,hashlib,json,os,time
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--upload-receipt',type=Path,required=True);a=p.parse_args();D=Path('/Users/lance/Documents/pokerbots-pokerbench/experiments/fresh-final6-reserve-v2');R=Path('data/experiments/grpo5-fresh-final6-v2');R.mkdir(exist_ok=True);plan=json.loads((D/'plan.json').read_text());up=json.loads(a.upload_receipt.read_text());raw=(D/'tasks.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==plan['tasks_sha256'];tasks=[Task.model_validate_json(x)for x in raw.splitlines()];assert len(tasks)==6
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);dataset=up['dataset_name'];ids=up['task_ids'];assert c.datasets.get(dataset).task_count==6 and {x.id for x in c.datasets.active_tasks(dataset)}==set(ids)
for tid,t in zip(ids,tasks):
 rt=c.datasets.load_task(tid);assert rt.input==t.input and rt.env_params==t.env_params
pins={'incumbent':('infer_b0f5e9429b7e','ckpt_51eee61470f7'),'grpo5':('infer_af5fa217b570','ckpt_a7a227300baf'),'opponent':('infer_21f395f49bff','ckpt_23b6b6239f26')}
for label,(iid,ckpt)in pins.items():
 m=c.inference.get(iid);assert m.checkpoint_id==ckpt and m.version==1 and m.state=='ready'
freeze=R/'selection-freeze.json'
if not freeze.exists():freeze.write_text(json.dumps({'frozen_before_any_final_calls_at':time.time(),'selected_only':'grpo5','pins':pins,'child_cannot_replace_using_final':True,'root_final_release_GO':True,'dataset':dataset,'task_sha256':plan['tasks_sha256'],'identity':identity,'gates':{'both_complete':6,'mean_rank_gain_vsC':.5,'legal_min':.99,'all_legal_real_tools':True,'cleanup_accepted_min':.98,'wrong_tools_max':0,'critical_workplace_max':0},'limitations':'Smalln6 wide uncertainty; no superiority claim. Factual memory limitations diagnostic, not factual pass.','deadline':'45min each;one10min only>=4complete/allunfinished>=h15/fresh90s/noerrors;absolute55min and1655UTC'},indent=2)+'\n')
for label in ['incumbent','grpo5']:
 out=R/label;out.mkdir(exist_ok=True);receipt=out/'receipt.json'
 if receipt.exists():continue
 cfg=eval_config(dataset,deployment=pins[label][0],max_parallel=2);cfg.name='grpo5-fresh-final6-v2-'+label;cfg.description='ReleasedFINAL frozenparentGRPO5 versus incumbentC;exact6freshdeals/fixedbase20. No child substitution/selection from final.';cfg.max_retries=0;preflight_identity(c);run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r={'eval_id':run.eval_id,'submitted_at':time.time(),'dataset':dataset,'task_ids':ids,'task_sha256':plan['tasks_sha256'],'candidate':pins[label][0],'checkpoint':pins[label][1],'version':1,'opponent':pins['opponent'],'arm':label,'max_parallel':2,'identity':identity};receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
