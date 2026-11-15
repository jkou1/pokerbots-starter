"""Four fresh development games, separate from sealed final outcomes."""
import asyncio,hashlib,json,os,random,time
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task,Message
from vals_tools.eval import eval_config
from pokerbots_working_client import preflight_identity
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/base20-development-v1';ROOT.mkdir(parents=True,exist_ok=True);path=ROOT/'receipt.json'
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c)
opp=c.inference.get('infer_21f395f49bff');assert opp.checkpoint_id=='ckpt_23b6b6239f26' and opp.version==1
models={'incumbent':('infer_b0f5e9429b7e','ckpt_51eee61470f7'),'rl20':('infer_9efa1c614a32','ckpt_11e7c430069c')}
for key,(mid,ckpt) in models.items():assert c.inference.get(mid).checkpoint_id==ckpt
rng=random.Random(11_150_010);seeds=[rng.getrandbits(48) for _ in range(4)]
known=set()
for f in [Path('data/experiments/sealed-final-base20-v1/tasks.jsonl'),Path('data/experiments/fast-screen-v1/tasks.jsonl'),Path('data/experiments/platform-official30-v1/select/tasks.jsonl'),Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training/pokerbots-history-selfplay-ad74-v1/train.jsonl')]:
 if f.exists():
  for line in f.open():
   seed=json.loads(line).get('env_params',{}).get('seed')
   if seed is not None:known.add(seed)
assert len(set(seeds))==4 and not set(seeds)&known
framework={'problem':'RL20 fixed32 EV gain is promising but single-hand screen does not establish carried-stack game quality against a betting opponent.','hypothesis':'RL20 improves game placement and unclipped EV versus incumbent against fixed base20 without increased invalid actions.','targeted_change':'Policy checkpoint only; same frozen base20 inference ID, four identical fresh development seeds, official30hand format.','test':'Two native existing-deployment jobs, maxparallel2 each, no retries, zero additional GPU; compare matched raw EV, place, busts, invalid actions and cleanup.','success_criteria':'Directional matched gains with no material reliability regression justify candidate consideration; four games are noisy, not proof.','stop_criteria':'Stop/repair technical failures or stalled requests; no live harness/model/opponent changes; no promotion based solely on clipped reward.','final_separation':'All four seeds disjoint sealed final six; do not inspect sealed outcomes.'}
(ROOT/'framework.json').write_text(json.dumps(framework,indent=2)+'\n')
tasks=[Task(input=[Message(role='user',content=f'Play an official six-seat no-limit hold em game for 30 hands from seat {i}.')],env_params={'preset':'event','seed':seed,'seats':6,'total_hands':30,'policy_seats':[i],'submit_fields':['action','amount'],'opponent_model':opp.id,'opponent_timeout_seconds':120,'decision_timeout_seconds':300,'ev_labels':True,'ev_runouts':64},tags={'split':'select','release':'base20-development-v1'}) for i,seed in enumerate(seeds)]
raw='\n'.join(t.model_dump_json() for t in tasks)+'\n';(ROOT/'tasks.jsonl').write_text(raw);digest=hashlib.sha256(raw.encode()).hexdigest();name='pokerbots-overnight-base20-development-v1'
r=json.loads(path.read_text()) if path.exists() else {'dataset':name,'sha256':digest,'seeds':seeds,'identity_preflight':identity,'frozen_opponent':{'inference_id':opp.id,'checkpoint':opp.checkpoint_id,'version':opp.version},'runs':{},'framework':framework};assert r['sha256']==digest
save=lambda:path.write_text(json.dumps(r,indent=2)+'\n')
if 'task_ids' not in r:
 existing={d.name:d for d in c.datasets.list()}
 if name in existing and not r.get('dataset_id'):raise RuntimeError('Existing dataset without local receipt')
 if name not in existing:
  preflight_identity(c);r['dataset_id']=c.datasets.create(name,description='Four fresh official30hand development games vs frozen base20; separate from final holdout.').id;save()
 preflight_identity(c);r['task_ids']=c.datasets.add_tasks(name,tasks=tasks);save()
assert {x.id for x in c.datasets.active_tasks(name)}==set(r['task_ids']) and c.datasets.get(name).task_count==4
for i in range(4):
 loaded=c.datasets.load_task(r['task_ids'][i]);assert loaded.input==tasks[i].input and loaded.env_params==tasks[i].env_params
r['verified_membership']=True;save()
for key,(mid,ckpt) in models.items():
 if key in r['runs']:continue
 current=c.inference.get(mid);assert current.checkpoint_id==ckpt
 preflight_identity(c);cfg=eval_config(name,deployment=mid,max_parallel=2);cfg.name=f'overnight-development-{key}-vs-base20';cfg.description='Matched four fresh official30hand development games, frozen base20 opponent, raw EV/place/reliability selection. No extraGPU; distinct sealed final.';cfg.max_retries=0
 run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r['runs'][key]={'eval_id':run.eval_id,'inference_id':mid,'checkpoint':ckpt,'version':current.version,'name':cfg.name,'submitted_at':time.time(),'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id};save();print(json.dumps(r['runs'][key]),flush=True)
