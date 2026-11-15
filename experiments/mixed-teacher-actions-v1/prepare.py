"""Validate canonical single-target tasks; freeze a balanced fast selection set."""
import hashlib,json,random,sys
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.training import supervised_task
from ac2.sdk.run_config import *
ROOT=Path(__file__).resolve().parent
read=lambda p:[json.loads(x) for x in p.open()]
def proportional(rows,n,seed):
 strata=defaultdict(list)
 for r in rows:strata[(r['provenance']['street'],r['target']['action'])].append(r)
 exact={k:len(v)*n/len(rows) for k,v in strata.items()};counts={k:int(v) for k,v in exact.items()}
 for k in sorted(exact,key=lambda k:(-(exact[k]-counts[k]),k))[:n-sum(counts.values())]:counts[k]+=1
 selected=[]
 for k,items in sorted(strata.items()):random.Random(seed).shuffle(items);selected+=items[:counts[k]]
 return selected

def main():
 quality=json.loads((ROOT/'quality.json').read_text());splits={s:read(ROOT/f'{s}.jsonl') for s in ['train','select','eval']}
 canonical=quality['canonical_teachers'];fast=[]
 for teacher in canonical:
  rows=[r for r in splits['select'] if r['provenance']['teacher']==teacher]
  fast+=proportional(rows,min(128,len(rows)),42)
 random.Random(42).shuffle(fast);(ROOT/'fast-select.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in fast))
 tasks={};stats={}
 for split,rows in {**splits,'fast-select':fast}.items():
  built=[];counts=Counter();unique=set();canonical_identity_in_prompt=0
  for r in rows:
   assert r['tool']=='submit_action' and set(r['target'])<={'action','amount'}
   assert all(x['role'] in ['system','user'] for x in r['input'])
   text='\n'.join(x['content'] for x in r['input'])
   assert not any(x in text for x in ['stack_after','Final board:','Showdown:','Stacks now:'])
   canonical_identity_in_prompt+=any(t in text for t in canonical)
   t=supervised_task(r);built.append(t);counts[(r['provenance']['teacher'],r['provenance']['street'],r['target']['action'])]+=1
   unique.add((r['provenance']['match_id'],r['provenance']['hand'],r['provenance']['action_index'],r['provenance']['teacher']))
  assert canonical_identity_in_prompt==0 and len(unique)==len(rows)
  (ROOT/f'{split}-tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n' for t in built));tasks[split]=built
  stats[split]={'records':len(rows),'unique_source_decisions':len(unique),'teachers':dict(Counter(r['provenance']['teacher'] for r in rows)),'streets':dict(Counter(r['provenance']['street'] for r in rows)),'actions':dict(Counter(r['target']['action'] for r in rows)),'canonical_teacher_ids_in_prompt':canonical_identity_in_prompt,'target_characters_by_teacher':{teacher:sum(len(json.dumps(r['target'])) for r in rows if r['provenance']['teacher']==teacher) for teacher in canonical},'task_file_sha256':hashlib.sha256((ROOT/f'{split}-tasks.jsonl').read_bytes()).hexdigest()}
 # Base initialization prevents prior SFT source exposure from contaminating
 # this experiment's new whole-match holdout. This file never launches a job.
 c=RunConfig(model='Qwen/Qwen3.6-35B-A3B',name='mixed-pete-carlos-actions-v1-base-sft-10steps-b128',description='One mixed-teacher action-only base pilot.7640balancedunique labels;whole-match/deal holdouts;10updates;checkpoint5/10;noautomaticextension.',tags={'stage':'mixed-teacher-actions','initialization':'base','dataset':'pokerbots-mixed-pete-carlos-actions-v1-train','teacher_mix':'50percentPete50percentCarlos','initial_max_updates':10,'requires_milestone_validation':True},experiment_cfg=ExperimentConfig(method=SFTConfig(),step=StepConfig(num_train_steps=10,problem_batch_size=128,checkpoint_interval=5,samples_per_problem=1,seed=42),tasks=TasksConfig(datasets=(TrainDatasetConfig(ac2_dataset_name='pokerbots-mixed-pete-carlos-actions-v1-train'),)),rollout=RolloutConfig(n_inference_replicas=0,max_total_len=8192),eval=EvalConfig(mode='off'),trainer=TrainerConfig(learning_rate=5e-6)),internal_cfg=InternalConfig(launch=InternalLaunchConfig(n_training_replicas=1,tensorboard_enabled=True)))
 (ROOT/'proposed-config.json').write_text(json.dumps(c.to_json(),indent=2)+'\n')
 (ROOT/'prepared.json').write_text(json.dumps({'stats':stats,'base_initialization':True,'proposed_budget':{'gpus':4,'replicas':1,'updates':10,'batch':128,'sample_budget':1280,'checkpoint_updates':[5,10],'learning_rate':5e-6,'rollout_replicas':0,'eval':'off'},'no_gpu_launch':True,'limitations':['Public private memory is unavailable; inputs are reconstructed decision-time states, not exact private conversations.','Both teachers influence observed action frequencies; imitation is not proof of optimal poker.','Teacher-balanced examples do not guarantee equal target-token weighting.']},indent=2)+'\n')
 print(json.dumps({'stats':stats,'proposed_gpus':4,'updates':10,'batch':128,'sample_budget':1280,'no_gpu_launch':True},indent=2))
if __name__=='__main__':main()
