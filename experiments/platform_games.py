"""Visible AC2 BYOH official30hand evaluation on existing deployments: zero new GPUs."""
import argparse,asyncio,hashlib,json,os
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task,Message
from vals_tools.collect_policy import deal_seeds
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/platform-official30-v1'
PVER='pver_3b0aae1bdaea'

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['select','eval'],default='select');p.add_argument('--model');p.add_argument('--label');p.add_argument('--prepare',action='store_true');p.add_argument('--launch',action='store_true');p.add_argument('--chosen-final',action='store_true');a=p.parse_args()
 if a.split=='eval' and a.launch and not a.chosen_final:raise ValueError('Choose one candidate before touching final holdout')
 if a.launch and (not a.model or not a.label):raise ValueError('model and unique label required for launch')
 name='pokerbots-overnight-official30-frozen-'+a.split+'-v1';out=ROOT/a.split;out.mkdir(parents=True,exist_ok=True)
 seeds=deal_seeds(a.split,6);tasks=[]
 for i,seed in enumerate(seeds):
  tasks.append(Task(input=[Message(role='user',content=f'Play an official six-seat30hand game from seat{i%6}.')],env_params={'preset':'event','seed':seed,'seats':6,'total_hands':30,'policy_seats':[i%6],'submit_fields':['action','amount'],'opponent_model':'vals-hackathon/selfplay-ad74c826c9ad','opponent_timeout_seconds':120,'decision_timeout_seconds':300,'ev_labels':True,'ev_runouts':64},tags={'split':a.split,'benchmark':'overnight-official30','opponent_checkpoint':'ckpt_ad74c826c9ad'}))
 raw='\n'.join(t.model_dump_json() for t in tasks)+'\n';digest=hashlib.sha256(raw.encode()).hexdigest();(out/'tasks.jsonl').write_text(raw);receipt=out/'receipt.json';r=json.loads(receipt.read_text()) if receipt.exists() else {'dataset':name,'sha256':digest,'evaluations':{}}
 if r['sha256']!=digest:raise ValueError('Task payload changed; use new dataset version')
 def save():receipt.write_text(json.dumps(r,indent=2)+'\n')
 if not(a.prepare or a.launch):print(json.dumps({'dataset':name,'tasks':6,'seeds':seeds,'sha256':digest,'gpu_allocation':0},indent=2));return
 c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);r['identity_preflight']=identity
 if 'task_ids' not in r:
  existing={d.name:d for d in c.datasets.list()}
  if name in existing and not r.get('dataset_id'):raise RuntimeError('Existing dataset has no local receipt; inspect before retry')
  if name not in existing:
   preflight_identity(c);d=c.datasets.create(name,description='Official30hand paired selection; fixed frozen ad74; six balanced policy seats; existing deployments only.');r['dataset_id']=d.id;save()
  preflight_identity(c);r['task_ids']=c.datasets.add_tasks(name,tasks=tasks);save()
 refs=c.datasets.active_tasks(name);remote=c.datasets.get(name)
 if len(refs)!=6 or {x.id for x in refs}!=set(r['task_ids']) or remote.task_count!=6:raise RuntimeError('Remote membership mismatch')
 for i in [0,3,5]:
  loaded=c.datasets.load_task(r['task_ids'][i])
  if loaded.input!=tasks[i].input or loaded.env_params!=tasks[i].env_params:raise RuntimeError('Uploaded task content mismatch')
 r['verified_membership']=True;r['verified_content_indices']=[0,3,5];save()
 if not a.launch:print('prepared_verified',name,flush=True);return
 if a.label in r['evaluations']:print(json.dumps(r['evaluations'][a.label]),flush=True);return
 preflight_identity(c);config=eval_config(name,deployment=a.model,max_parallel=2);config.name='overnight-official30-'+a.label+'-'+a.split;config.description='Six official30hand paired games with carry stacks; frozen ad74 opponents; existing deployment, zero extraGPU. Source logs retained on local harness.';config.max_retries=0;run=asyncio.run(c.eval.run(config,project_version_id=PVER));eid=run.eval_id
 r['evaluations'][a.label]={'eval_id':eid,'model':a.model,'name':config.name,'identity_preflight':identity,'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+eid};save();print(json.dumps(r['evaluations'][a.label]),flush=True)
if __name__=='__main__':main()
