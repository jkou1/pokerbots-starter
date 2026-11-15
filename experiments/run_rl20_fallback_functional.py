"""One reused TRAIN-only functional game, no new final or quality selection."""
import asyncio,json,os,time,threading
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
R=Path('data/experiments');serving=json.loads((R/'rl20-fallback-serving.json').read_text());assert serving['ready_verified'];D=Path('/Users/lance/Documents/pokerbots-pokerbench/experiments/rl20-restored-functional-source-v1');task=Task.model_validate_json((D/'task.jsonl').read_text().strip());c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);m=c.inference.get(serving['inference_id']);assert m.state=='ready' and m.checkpoint_id=='ckpt_11e7c430069c' and m.version==1;name='pokerbots-rl20-restored-functional-train-reuse-v1';assert c.datasets.get(name).task_count==1;rt=c.datasets.load_task('tsk_0f7081400598');assert rt.input==task.input and rt.env_params==task.env_params;out=R/'rl20-fallback-functional';out.mkdir(exist_ok=True);p=out/'receipt.json';assert not p.exists()
cfg=eval_config(name,deployment=m.id,max_parallel=1);cfg.name='rl20-restored-functional-train-reuse-one';cfg.description='One exact previously used TRAIN30hand case, deployment-to-grading/tools/cleanup/SAY only; no newFINAL/qualityranking.';cfg.max_retries=0;preflight_identity(c);run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r={'eval_id':run.eval_id,'inference_id':m.id,'checkpoint':m.checkpoint_id,'version':1,'submitted_at':time.time(),'identity':identity,'source_task':'tsk_0f7081400598','dataset':name,'purpose':'FUNCTIONAL_ONLY_TRAIN_REUSE_NO_RANKING'};r['deadline']=r['submitted_at']+900;p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
gc=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);preflight_identity(gc);done=threading.Event()
def stop():
 if not done.is_set():gc.eval.stop(run.eval_id);(out/'stop.json').write_text(json.dumps({'at':time.time(),'reason':'15minutehardcap'})+'\n')
timer=threading.Timer(max(0,r['deadline']-time.time()),stop);timer.start()
try:
 while True:
  live=c.eval.get(run.eval_id);(out/'progress.json').write_text(json.dumps({'at':time.time(),'status':live.status,'eval_id':run.eval_id,'job_id':live.job_id})+'\n')
  if live.status in ['succeeded','failed','stopped','cancelled']:done.set();break
  time.sleep(15)
finally:done.set();timer.cancel()
