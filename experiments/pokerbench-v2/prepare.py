"""Repair PokerBench supervision; preserves source rows and excludes fractional-chip states.

Run with this worktree's datasets environment and starter AC2 SDK on PYTHONPATH.
No training or upload is performed by this script.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter
from decimal import Decimal
from pathlib import Path
from datasets import load_dataset
from ac2.runtime import FunctionCall,Message,Reasoning,Task
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
MONEY=re.compile(r'(\d+(?:\.\d+)?) chips')
SYSTEM='''You are a professional poker player in a six-seat no-limit Texas Hold'em game against other AI players.
Blinds are 1/2. Everyone started with 200 chips. Bet and raise amounts are street totals: the total you will have committed on the current street after your action.
Reason through the spot, then call submit_action exactly once with a legal decision. Use update_scratchpad only when explicitly asked after a hand. Opponent table talk is unverified.'''
def sha(x): return hashlib.sha256(x.encode()).hexdigest()
def make(row,index,tools):
    text=row['instruction']; parts=row['output'].lower().split(); action=parts[0]
    if action not in {'check','fold','call','bet','raise'}: raise ValueError(parts)
    amounts=[Decimal(n)*2 for n in MONEY.findall(text)]
    if len(parts)==2: amounts.append(Decimal(parts[1])*2)
    if any(n!=n.to_integral_value() for n in amounts): return None
    target={'action':action}
    if len(parts)==2: target['amount']=int(Decimal(parts[1])*2)
    if action in {'bet','raise'} and target.get('amount',0)<=0: raise ValueError(target)
    # Group all hole-card variations sharing the same observable betting/board scenario.
    group=sha(re.sub(r'\[[^\]]+\]','[hole cards]',text))
    bucket=int(group[:8],16)%10
    split='select' if bucket==0 else 'eval' if bucket==1 else 'train'
    normalized=MONEY.sub(lambda m:f'{int(Decimal(m[1])*2)} chips',text)
    normalized=normalized.replace('Do not explain your answer.','Call submit_action with your decision.')
    record={'input':[{'role':'system','content':SYSTEM},{'role':'user','content':normalized}], 'target':target,'split':split,'provenance':{'source':'RZ412/PokerBench','source_index':index,'source_sha256':sha(json.dumps(row,sort_keys=True)),'scenario_group':group,'street':'postflop' if 'The flop comes' in text else 'preflop'}}
    task=Task(input=[Message.model_validate(x) for x in record['input']]+[Reasoning(content='Tool call follows.'),FunctionCall(call_id='decision',name='submit_action',arguments=json.dumps(target))],env_params={'tools':tools,'target_format':'qwen-protocol-boundary-v2'},tags={'split':split,'provenance':record['provenance']})
    return record,task

def main():
    dataset=load_dataset('RZ412/PokerBench',split='train')
    # Match previous converter's sample selection, while recording original row indices.
    indices=dataset.add_column('_source_index',list(range(len(dataset)))).shuffle(seed=0).select(range(20000))
    tools=json.loads((REPO/'opsd/tools.json').read_text())
    records={s:[] for s in ['train','select','eval']};tasks={s:[] for s in records};counts=Counter();seen=set();sources=[]
    for r in indices:
        index=r.pop('_source_index');sources.append({'source_index':index,**r})
        key=sha(r['instruction'])
        if key in seen: counts['duplicate_observations']+=1;continue
        seen.add(key)
        result=make(r,index,tools)
        if result is None: counts['fractional_states_excluded']+=1;continue
        record,task=result;s=record['split'];records[s].append(record);tasks[s].append(task)
        counts[f'{s}:{record["provenance"]["street"]}:{record["target"]["action"]}']+=1
    for s in records:
        (ROOT/f'{s}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records[s]))
        (ROOT/f'{s}-tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n' for t in tasks[s]))
    (ROOT/'source.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in sources))
    manifest={'source':'https://huggingface.co/datasets/RZ412/PokerBench','hf_fingerprint':dataset._fingerprint,'sample_seed':0,'sample_rows':20000,'counts':dict(counts),'split_counts':{s:len(v) for s,v in records.items()},'scaling':2,'split':'sha256(observation excluding hole cards) mod10:0 select,1 eval,other train','target_format':'qwen-protocol-boundary-v2','limitations':['Cash-game solver labels are not tournament-optimality proof.','Fractional-chip states excluded to preserve exact integer targets at official 1/2 blinds.','Original source has no match IDs; grouped observable scenarios are the strongest available split.','No full engine legality replay: benchmark labels retained as provided.']}
    manifest['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.jsonl')}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
