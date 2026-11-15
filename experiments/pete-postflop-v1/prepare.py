"""Prepare 75:25 new postflop/preflop preservation mix; no training launch."""
import json,random,hashlib,sys
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.training import supervised_task
from ac2.sdk.run_config import *
from ac2.sdk.model import ModelConfig
ROOT=Path(__file__).resolve().parent
read=lambda p:[json.loads(l) for l in p.open()]
allgroups={}
for split in ['train','select','eval']:
 post=read(ROOT/f'{split}.jsonl');pre=read(ROOT/f'preflop-{split}.jsonl')
 allgroups[split]={r['deal_identity'] for r in post+pre}
 rows=post
 if split=='train':
  # Unique preservation targets; do not duplicate examples to simulate coverage.
  random.Random(42).shuffle(pre);rows=post+pre[:round(len(post)/3)];random.Random(42).shuffle(rows)
  (ROOT/'mixed-train.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 tasks=[supervised_task(r) for r in rows]
 (ROOT/f'{split}-tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n' for t in tasks))
 print(split,len(rows),sum(r['provenance']['street']!='preflop' for r in rows),'postflop')
for a,b in [('train','select'),('train','eval'),('select','eval')]:assert not allgroups[a]&allgroups[b]
c=RunConfig(model=ModelConfig(checkpoint='ckpt_51eee61470f7'),name='pete-postflop-v1-incumbent-sft-40steps-lr2e6',description='109 replay-validated Pete matches.1250 postflop+417 unique preflop preservation train examples;75:25 mix;deal-heldout select147 eval103 postflop;protocol boundary v2.',tags={'stage':'pete-postflop','parent_checkpoint':'ckpt_51eee61470f7','dataset':'pokerbots-pete-postflop-v1-train','hypothesis':'broaden postflop value extraction with strongest public teacher'},experiment_cfg=ExperimentConfig(method=SFTConfig(),step=StepConfig(num_train_steps=40,problem_batch_size=64,checkpoint_interval=20,samples_per_problem=1,seed=42),tasks=TasksConfig(datasets=(TrainDatasetConfig(ac2_dataset_name='pokerbots-pete-postflop-v1-train'),)),rollout=RolloutConfig(n_inference_replicas=0,max_total_len=8192),eval=EvalConfig(mode='off'),trainer=TrainerConfig(learning_rate=2e-6)),internal_cfg=InternalConfig(launch=InternalLaunchConfig(n_training_replicas=1,tensorboard_enabled=True)))
(ROOT/'pilot-config.json').write_text(json.dumps(c.to_json(),indent=2)+'\n')
print('Config prepared; deal splits disjoint.')
