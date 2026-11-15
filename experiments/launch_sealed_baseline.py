"""Launch only the incumbent's operationally sealed final baseline; never read outcomes."""
import asyncio,hashlib,json,os,random,time
from pathlib import Path
import httpx
from ac2.sdk import Client
from ac2.runtime import Task,Message
from vals_tools.eval import eval_config
from vals_tools.deploy import INFERENCE_URL,PROBE_MESSAGES,PROBE_TOOL
from pokerbots_working_client import preflight_identity
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/sealed-final-base20-v1';ROOT.mkdir(parents=True,exist_ok=True);path=ROOT/'receipt.json';c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);opponent=c.inference.get('infer_21f395f49bff');assert opponent.checkpoint_id=='ckpt_23b6b6239f26' and opponent.version==1 and opponent.state in ['ready','running','healthy']
if path.exists() and json.loads(path.read_text()).get('baseline',{}).get('eval_id'):
 print(json.dumps(json.loads(path.read_text())['baseline']));raise SystemExit
probe=httpx.post(INFERENCE_URL+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['AC2_API_KEY']},json={'model':opponent.id,'messages':PROBE_MESSAGES,'tools':[PROBE_TOOL],'max_completion_tokens':5000,'chat_template_kwargs':{'enable_thinking':True}},timeout=60);probe.raise_for_status();assert probe.json()['choices'][0]['message'].get('tool_calls')
rng=random.Random(11_150_009);seeds=[rng.getrandbits(48) for _ in range(6)];assert len(set(seeds))==6
known=set()
for f in [Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training/pokerbots-history-selfplay-ad74-v1/train.jsonl'),Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/fast-screen-v1/tasks.jsonl'),Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/platform-official30-v1/select/tasks.jsonl')]:
 if f.exists():
  for line in f.open():
   value=json.loads(line).get('env_params',{}).get('seed')
   if value is not None:known.add(value)
assert not set(seeds)&known
tasks=[Task(input=[Message(role='user',content=f'Play an official six-seat no-limit hold em game for 30 hands from seat {i}.')],env_params={'preset':'event','seed':seed,'seats':6,'total_hands':30,'policy_seats':[i],'submit_fields':['action','amount'],'opponent_model':opponent.id,'opponent_timeout_seconds':120,'decision_timeout_seconds':300,'ev_labels':True,'ev_runouts':64},tags={'split':'eval','release':'sealed-final-base20-v1','outcomes_sealed':True}) for i,seed in enumerate(seeds)];raw='\n'.join(t.model_dump_json() for t in tasks)+'\n';(ROOT/'tasks.jsonl').write_text(raw);digest=hashlib.sha256(raw.encode()).hexdigest();name='pokerbots-overnight-base20-final-v1';r=json.loads(path.read_text()) if path.exists() else {'dataset':name,'sha256':digest,'outcomes_sealed':True,'selected_candidate':None,'identity_preflight':identity,'frozen_opponent':{'inference_id':opponent.id,'model':'vals-hackathon/'+opponent.name,'checkpoint':opponent.checkpoint_id,'version':opponent.version},'seeds':seeds,'created_at':time.time(),'seal_policy':'No score queries or poker-outcome inspection until one candidate is selected from selection evidence.'};assert r['sha256']==digest

def save():path.write_text(json.dumps(r,indent=2)+'\n')
if 'task_ids' not in r:
 existing={d.name:d for d in c.datasets.list()}
 if name in existing and not r.get('dataset_id'):raise RuntimeError('Existing final dataset lacks a local receipt; do not append')
 if name not in existing:
  preflight_identity(c);d=c.datasets.create(name,description='Sealed final holdout: fresh six balanced official30hand games, frozen baseSFT20 opponents; no outcomes for selection.');r['dataset_id']=d.id;save()
 preflight_identity(c);r['task_ids']=c.datasets.add_tasks(name,tasks=tasks);save()
assert {x.id for x in c.datasets.active_tasks(name)}==set(r['task_ids']) and c.datasets.get(name).task_count==6
for i in [0,3,5]:
 loaded=c.datasets.load_task(r['task_ids'][i]);assert loaded.input==tasks[i].input and loaded.env_params==tasks[i].env_params
r.update(verified_membership=True,verified_content_indices=[0,3,5]);save();current=c.inference.get(opponent.id);assert current.version==opponent.version and current.checkpoint_id==opponent.checkpoint_id
preflight_identity(c);cfg=eval_config(name,deployment='vals-hackathon/combined-sft-v3',max_parallel=2);cfg.name='overnight-sealed-final-incumbent-vs-base20';cfg.description='Incumbent baseline only. Fresh6 official30hand games vs immutable baseSFT20 inferenceID; outcomes operationally sealed until candidate selection. Zero extraGPU.';cfg.max_retries=0;run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r['baseline']={'eval_id':run.eval_id,'model':'vals-hackathon/combined-sft-v3','checkpoint':'ckpt_51eee61470f7','name':cfg.name,'identity_preflight':identity,'submitted_at':time.time(),'dashboard':'https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id};save();(ROOT/'FROZEN_DEPENDENCY.json').write_text(json.dumps({'reason':'Frozen opponent for sealed final baseline and selected-candidate comparison','inference_id':opponent.id,'checkpoint':opponent.checkpoint_id,'version':opponent.version,'do_not_retire_or_change_until_holdout_complete':True},indent=2));print(json.dumps(r['baseline']),flush=True)
