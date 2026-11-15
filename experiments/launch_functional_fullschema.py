"""One fresh full-LOCAL-default-schema30hand functional smoke, not a performance rerun."""
import asyncio,json,os,random,time
from pathlib import Path
from ac2.sdk import Client
from ac2.runtime import Task,Message
from vals_tools.eval import eval_config
from poker_harness.prompts import table_tools,talk_fields
from pokerbots_working_client import preflight_identity
ROOT=Path(__file__).resolve().parent.parent/'data/experiments';out=ROOT/'fullschema-functional30/rl20';out.mkdir(parents=True,exist_ok=True);path=out/'receipt.json'
if path.exists() and json.loads(path.read_text()).get('eval_id'):print(json.dumps(json.loads(path.read_text())));raise SystemExit
stress=json.loads((ROOT/'cleanup-stress-results/rl20.json').read_text());assert stress['status']=='complete','Existing stress requests must finish first'
framework={'problem':'Reduced-schema performance comparisons omit p_win/read; deployment should also be checked with optional local diagnostic fields.','hypothesis':'RL20 retains legal real submit_action and cleanup behavior with full LOCAL default action/amount/p_win/read/say schema.','targeted_change':'One fresh official30hand task, omit submit_fields override; unmodified event tools, sanitizer, caps, carried stacks. Existing immutable RL20 policy and frozen base20 opponents.','test':'Native existing-deployment eval, parallel1,retries0,zero extraGPU; raw logs audit actual tool validity, sizing, cleanup acceptance and raw/sanitized talk.','success':'Completed official grading with full tool schema and no material protocol/legality failure; bounded workplace review covers emitted talk. This one game is functional evidence, not a performance estimate.','stop':'Investigate setup/transport/stall failures or malformed tools; do not change active harness/schema/caps or inspect sealed outcomes.'}
(out/'framework.json').write_text(json.dumps(framework,indent=2)+'\n')
c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);model=c.inference.get('infer_9efa1c614a32');assert model.checkpoint_id=='ckpt_11e7c430069c' and model.version==1;opp=c.inference.get('infer_21f395f49bff');assert opp.checkpoint_id=='ckpt_23b6b6239f26' and opp.version==1
fields=list(table_tools(talk_fields(None),scratchpad=True)[0]['function']['parameters']['properties']);assert fields==['action','amount','p_win','read','say']
seed=random.Random(11_150_011).getrandbits(48);known=set()
for f in [ROOT/'sealed-final-base20-v1/tasks.jsonl',ROOT/'base20-development-v1/tasks.jsonl',ROOT/'platform-official30-v1/select/tasks.jsonl',ROOT/'fast-screen-v1/tasks.jsonl',Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training/pokerbots-history-selfplay-ad74-v1/train.jsonl')]:
 if f.exists():
  for line in f.open():known.add(json.loads(line).get('env_params',{}).get('seed'))
assert seed not in known
task=Task(input=[Message(role='user',content='Play an official six-seat no-limit hold em game for30hands from seat4.')],env_params={'preset':'event','seed':seed,'seats':6,'total_hands':30,'policy_seats':[4],'opponent_model':opp.id,'opponent_timeout_seconds':120,'decision_timeout_seconds':300,'ev_labels':True,'ev_runouts':64},tags={'split':'select','purpose':'functional-fullschema-smoke'})
name='pokerbots-overnight-fullschema-functional30-v1';r=json.loads(path.read_text()) if path.exists() else {'dataset':name,'seed':seed,'policy_seat':4,'inference_id':model.id,'checkpoint':model.checkpoint_id,'version':model.version,'opponent_inference_id':opp.id,'opponent_checkpoint':opp.checkpoint_id,'opponent_version':opp.version,'submit_fields_override':None,'effective_submit_fields':fields,'identity_preflight':identity};save=lambda:path.write_text(json.dumps(r,indent=2)+'\n');(out/'task.json').write_text(task.model_dump_json(indent=2))
if 'task_ids' not in r:
 existing={d.name:d for d in c.datasets.list()}
 if name in existing and not r.get('dataset_id'):raise RuntimeError('Existing dataset without receipt; no blind append')
 if name not in existing:preflight_identity(c);r['dataset_id']=c.datasets.create(name,description='One fresh full-official-schema30hand functional gate, not poker quality ranking.').id;save()
 preflight_identity(c);r['task_ids']=c.datasets.add_tasks(name,tasks=[task]);save()
assert len(r['task_ids'])==1 and {x.id for x in c.datasets.active_tasks(name)}==set(r['task_ids']) and c.datasets.get(name).task_count==1
loaded=c.datasets.load_task(r['task_ids'][0]);assert loaded.input==task.input and loaded.env_params==task.env_params;r['verified_membership_and_content']=True;save()
preflight_identity(c);cfg=eval_config(name,deployment=model.id,max_parallel=1);cfg.name='overnight-grpo-step20-fullschema-functional30';cfg.description='Full default submit_action action/amount/p_win/read/say, official event cleanup/sanitizer/caps unchanged. Fresh single30hand functional gate, not performance evidence. Zero extraGPU.';cfg.max_retries=0
run=asyncio.run(c.eval.run(cfg,project_version_id='pver_3b0aae1bdaea'));r.update(eval_id=run.eval_id,submitted_at=time.time(),dashboard='https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/'+run.eval_id);save();print(json.dumps(r),flush=True)
