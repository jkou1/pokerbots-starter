"""Resumable preparation/launch of paired deployment evals; no new inference engines."""
from __future__ import annotations
import argparse,asyncio,hashlib,json
from pathlib import Path
from ac2.sdk import Client
from vals_tools.tasks import hand_tasks,Opponents
from vals_tools.eval import eval_config

ROOT=Path(__file__).resolve().parent.parent/'data/experiments/fast-screen-v1'
NAME='pokerbots-overnight-fast-select-v1'
MODELS=['vals-hackathon/combined-sft-v3','vals-hackathon/selfplay-ad74c826c9ad']

def main():
 p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');p.add_argument('--parallel',type=int,default=2);a=p.parse_args()
 ROOT.mkdir(parents=True,exist_ok=True)
 tasks=hand_tasks(32,771150033,Opponents(model=MODELS[1],api='chat',reasoning_effort=None,timeout_seconds=120))
 raw='\n'.join(t.model_dump_json() for t in tasks)+'\n';digest=hashlib.sha256(raw.encode()).hexdigest();(ROOT/'tasks.jsonl').write_text(raw)
 receipt_path=ROOT/'receipt.json';r=json.loads(receipt_path.read_text()) if receipt_path.exists() else {'name':NAME,'sha256':digest,'models':{}}
 if r['sha256']!=digest:raise RuntimeError('task hash changed')
 def save():receipt_path.write_text(json.dumps(r,indent=2)+'\n')
 if not a.launch:print(json.dumps({'dataset':NAME,'tasks':len(tasks),'sha256':digest,'models':MODELS,'max_parallel':a.parallel},indent=2));return
 c=Client(project='vals-hackathon')
 if 'task_ids' not in r:
  if any(d.name==NAME for d in c.datasets.list()):raise RuntimeError('dataset exists without local upload receipt; inspect membership before retry')
  c.datasets.create(NAME,description='Frozen ad74 paired32hand selection; fresh seeds; no GPU engine allocation.')
  r['task_ids']=c.datasets.add_tasks(NAME,tasks=tasks);save()
 for model in MODELS:
  if model in r['models']:continue
  config=eval_config(NAME,deployment=model,max_parallel=a.parallel)
  config.name='overnight-fast-'+model.split('/')[-1]
  run=asyncio.run(c.eval.run(config));r['models'][model]=str(getattr(run,'eval_id',run));save();print(model,r['models'][model],flush=True)
if __name__=='__main__':main()
