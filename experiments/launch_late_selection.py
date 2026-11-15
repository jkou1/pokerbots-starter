"""One fresh64 native BYOH selection per approved checkpoint; no GPU deployment here."""
import argparse,asyncio,hashlib,json,os,time
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--label',choices=['step20','step100','step95','step40'],required=True);p.add_argument('--inference',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--capacity-receipt',type=Path,required=True);a=p.parse_args();ROOT=Path(__file__).resolve().parent.parent/'data/experiments/late-grpo-fresh64-v1';manifest=json.loads((ROOT/'manifest.json').read_text());clearance=json.loads(a.capacity_receipt.read_text());assert all(clearance.get(k)is True for k in ['grpo_gpus_released','mixed_four_gpus_running','final_requests_drained','protected_serving_verified']);
if a.label=='step95':assert clearance.get('root_fallback95_approved')is True,'No implicit95 fallback'
raw=(ROOT/'tasks.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['sha256'];tasks=[Task.model_validate(json.loads(x))for x in raw.splitlines()];path=ROOT/'receipt.json';r=json.loads(path.read_text())if path.exists()else {'dataset':manifest['dataset'],'sha256':manifest['sha256'],'evaluations':{},'capacity_receipt':str(a.capacity_receipt.resolve()),'capacity_receipt_sha256':hashlib.sha256(a.capacity_receipt.read_bytes()).hexdigest()};assert r['sha256']==manifest['sha256']
if a.label in r['evaluations']:
 old=r['evaluations'][a.label];assert old['inference_id']==a.inference and old['checkpoint']==a.checkpoint;print(json.dumps(old));raise SystemExit
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);model=c.inference.get(a.inference);assert model.checkpoint_id==a.checkpoint and model.state in ['ready','running','healthy']
for opp in manifest['opponents'].values():
 actual=c.inference.get(opp['inference_id']);assert actual.checkpoint_id==opp['checkpoint'] and actual.version==opp['version']
final=json.loads((ROOT.parent/'sealed-final-base20-v1/receipt.json').read_text());assert c.eval.get(final['candidate']['eval_id']).status in ['succeeded','failed','stopped','cancelled']
save=lambda:path.write_text(json.dumps(r,indent=2)+'\n');name=manifest['dataset']
if 'task_ids'not in r:
 existing={d.name:d for d in c.datasets.list()}
 if name in existing and not r.get('dataset_id'):raise RuntimeError('Existing dataset has no local receipt; no blind append')
 if name not in existing:preflight_identity(c);r['dataset_id']=c.datasets.create(name,description='Fresh64 single-hand selection,32ad74/32base20, matched20/100/40 only. No final reuse; no clipped-reward quality claims.').id;save()
 preflight_identity(c);r['task_ids']=c.datasets.add_tasks(name,tasks=tasks);save()
assert len(r['task_ids'])==64 and c.datasets.get(name).task_count==64 and {x.id for x in c.datasets.active_tasks(name)}==set(r['task_ids'])
indices=sorted({0,31,32,63,*[next(x['index']for x in manifest['task_metadata']if x['opponent_stratum']==opp)for opp in manifest['opponents']]})
for i in indices:
 loaded=c.datasets.load_task(r['task_ids'][i]);assert loaded.input==tasks[i].input and loaded.env_params==tasks[i].env_params
r.update(verified_membership=True,verified_content_indices=indices);save();preflight_identity(c);cfg=eval_config(name,deployment=model.id,max_parallel=4);cfg.name=f'overnight-late-grpo-{a.label}-fresh64-select';cfg.description='Fresh64 paired single-hand selection versus fixed20, stratified32ad74/32base20. Unclipped EV, legal/protocol and stratum analysis; not carried-stack quality proof. Existing deployment0extraGPU.';cfg.max_retries=0;run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r['evaluations'][a.label]={'eval_id':run.eval_id,'inference_id':model.id,'checkpoint':model.checkpoint_id,'version':model.version,'identity_preflight':identity,'submitted_at':time.time(),'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id};save();print(json.dumps(r['evaluations'][a.label]),flush=True)
