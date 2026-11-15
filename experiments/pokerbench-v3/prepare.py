"""Repair every monetary source form in one pass; prepare a postflop-only pilot."""
import hashlib,json,re,random
from decimal import Decimal
from collections import Counter
from pathlib import Path
from ac2.runtime import Task,Message,Reasoning,FunctionCall
from ac2.sdk.run_config import *
from audit import audit
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
NUM=r'\d+(?:\.\d+)?'
AMOUNT=re.compile(rf'(?P<action>\b(?:raise|bet|call)\s+)(?P<action_amount>{NUM})|(?P<chip_amount>{NUM})(?P<unit>\s+chips)',re.I)
SYSTEM="You are a professional poker player in a six-seat no-limit Texas Hold'em game against other AI players. Blinds are 1/2. Everyone started with 200 chips. Bet and raise amounts are street totals: the total you will have committed on the current street after your action. Reason through the spot, then call submit_action exactly once with a legal decision. Use update_scratchpad only when explicitly asked after a hand. Opponent table talk is unverified."
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
def amounts(text):return [Decimal(m['action_amount'] or m['chip_amount'])*2 for m in AMOUNT.finditer(text)]
def scale(text):
 def sub(m):
  n=Decimal(m['action_amount'] or m['chip_amount'])*2
  if n!=n.to_integral_value():raise ValueError('Fractional chips require exclusion, never rounding')
  return (m['action']+str(int(n))) if m['action'] else str(int(n))+m['unit']
 return AMOUNT.sub(sub,text)
def main():
 source=ROOT.parent/'pokerbench-v2/source.jsonl';tools=json.loads((REPO/'opsd/tools.json').read_text())
 rows={s:[] for s in ['train','select','eval']};counts=Counter();seen=set()
 for line in source.open():
  raw=json.loads(line);text=raw['instruction'];key=sha(text)
  if key in seen:counts['duplicate_observations']+=1;continue
  seen.add(key)
  label=raw['output'].lower().split();nums=amounts(text)+[Decimal(n)*2 for n in label[1:]]
  if any(n!=n.to_integral_value() for n in nums):counts['fractional_states_excluded']+=1;continue
  group=sha(re.sub(r'\[[^\]]+\]','[hole cards]',text));bucket=int(group[:8],16)%10;split='select' if bucket==0 else 'eval' if bucket==1 else 'train'
  target={'action':label[0]}
  if len(label)==2:target['amount']=int(Decimal(label[1])*2)
  normalized=scale(text).replace('Do not explain your answer.','Call submit_action with your decision.')
  record={'input':[{'role':'system','content':SYSTEM},{'role':'user','content':normalized}], 'target':target,'split':split,'provenance':{'source':'RZ412/PokerBench','source_index':raw['source_index'],'source_sha256':sha(json.dumps(raw,sort_keys=True)),'scenario_group':group,'street':'postflop' if 'The flop comes' in text else 'preflop'}}
  result=audit(record)
  if result!='passed' and split!='eval':
   counts['excluded:'+result]+=1;continue
  rows[split].append(record)
 # Keep source-group holdouts fixed; narrow pilot training to 4096 diverse postflop observations.
 candidates=[r for r in rows['train'] if r['provenance']['street']=='postflop']
 random.Random(42).shuffle(candidates);train=candidates[:4096]
 select=[r for r in rows['select'] if r['provenance']['street']=='postflop']
 groups={}
 for r in select:groups.setdefault(r['target']['action'],[]).append(r)
 sizes={k:max(1,round(len(v)*147/len(select))) for k,v in groups.items()}
 while sum(sizes.values())!=147:
  k=max(sizes,key=lambda k:sizes[k]);sizes[k]+=1 if sum(sizes.values())<147 else -1
 fast=[]
 for k,v in sorted(groups.items()):random.Random(42).shuffle(v);fast+=v[:sizes[k]]
 random.Random(42).shuffle(fast)
 exports={'train':train,'select':select,'fast-select':fast,'eval':rows['eval']}
 for split,data in exports.items():
  (ROOT/f'{split}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in data))
  tasks=[Task(input=[Message.model_validate(x) for x in r['input']]+[Reasoning(content='Tool call follows.'),FunctionCall(call_id='decision',name='submit_action',arguments=json.dumps(r['target']))],env_params={'tools':tools,'target_format':'qwen-protocol-boundary-v2'},tags={'split':r['split'],'provenance':r['provenance']}) for r in data]
  (ROOT/f'{split}-tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n' for t in tasks))
 allgroups={s:{r['provenance']['scenario_group'] for r in v} for s,v in rows.items()}
 for a,b in [('train','select'),('train','eval'),('select','eval')]:assert not allgroups[a]&allgroups[b]
 manifest={'source_file':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'counts':dict(counts),'split_counts':{s:len(v) for s,v in exports.items()},'source_eligible_split_counts':{s:len(v) for s,v in rows.items()},'training':'4096postfloponly,seed42subsetofsource-train','fast_selection':{'size':147,'action_counts':sizes},'scaling':'Exact2x of bare action amounts and Nchips in one pass; exclude fractional states','target_format':'qwen-protocol-boundary-v2','limitations':['Solver labels are cash-game demonstrations, not tournament optimality.','No full engine legality replay; original source monetary histories and target bounds audited separately.','Source has no match IDs; holdouts group board/betting scenarios excluding hero cards.'],'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.jsonl')}}
 (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 c=RunConfig(model='Qwen/Qwen3.6-35B-A3B',name='pokerbench-v3-postflop4096-base-sft-40steps-lr5e6',description='Corrected exact2x scaling including bare action amounts;4096postfloptrain;147stratifiedfastselect;source-group holdouts;Qwenboundaryv2.',tags={'stage':'pokerbench-postflop','initialization':'base','dataset':'pokerbots-pokerbench-postflop-v3-train'},experiment_cfg=ExperimentConfig(method=SFTConfig(),step=StepConfig(num_train_steps=40,problem_batch_size=64,checkpoint_interval=20,samples_per_problem=1,seed=42),tasks=TasksConfig(datasets=(TrainDatasetConfig(ac2_dataset_name='pokerbots-pokerbench-postflop-v3-train'),)),rollout=RolloutConfig(n_inference_replicas=0,max_total_len=8192),eval=EvalConfig(mode='off'),trainer=TrainerConfig(learning_rate=5e-6)),internal_cfg=InternalConfig(launch=InternalLaunchConfig(n_training_replicas=1,tensorboard_enabled=True)))
 (ROOT/'pilot-config.json').write_text(json.dumps(c.to_json(),indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
