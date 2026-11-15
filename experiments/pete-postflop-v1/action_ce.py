"""Extract action/amount-only CE from managed SFT tokens; fixed syntax excluded."""
import argparse,collections,gzip,hashlib,json,math,re
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec
ACTION=re.compile(r'<parameter=action>\s*(fold|check|call|bet|raise)\s*</parameter>')
AMOUNT=re.compile(r'<parameter=amount>\s*([0-9]+)\s*</parameter>')

def token_ce(payload,span):
 starts=[];position=0
 for token in payload['sampled_tokens']:
  starts.append((position,position+len(token)));position+=len(token)
 indices=[i for i,(a,b) in enumerate(starts) if a<span[1] and b>span[0]]
 logs=payload['train_sampled_log_probs'];mask=payload['loss_mask']
 if not indices or any(mask[i]!=1 or logs[i] is None or not math.isfinite(logs[i]) for i in indices):raise ValueError('Missing supervised argument log probabilities')
 return sum(-logs[i] for i in indices)/len(indices),len(indices)

def arguments(payload):
 text=''.join(payload['sampled_tokens']);match=ACTION.search(text)
 if not match:raise ValueError('No unambiguous actual action argument')
 action_loss,action_n=token_ce(payload,match.span(1));result={'action':match[1],'action_ce':action_loss,'action_tokens':action_n}
 amount=AMOUNT.search(text)
 if amount:
  loss,n=token_ce(payload,amount.span(1));result.update(amount_ce=loss,amount_tokens=n,amount=int(amount[1]))
 return result

def summarize(rows):
 groups=collections.defaultdict(list)
 for row in rows:groups[row['action']].append(row)
 per={k:{'samples':len(v),'action_ce':sum(r['action_ce'] for r in v)/len(v)} for k,v in sorted(groups.items())}
 amount=[r for r in rows if 'amount_ce' in r]
 return {'samples':len(rows),'per_action':per,'class_balanced_action_ce':sum(r['action_ce'] for r in per.values())/len(per) if per else None,'micro_action_ce':sum(r['action_ce'] for r in rows)/len(rows) if rows else None,'amount_samples':len(amount),'amount_ce':sum(r['amount_ce'] for r in amount)/len(amount) if amount else None}

def main():
 p=argparse.ArgumentParser();p.add_argument('--train',required=True);p.add_argument('--name',required=True);args=p.parse_args()
 root=Path(__file__).resolve().parent;c=Client(project='vals-hackathon');offset=0;seen=set();data=[]
 raw=root/f'{args.name}-all-token-samples.jsonl.gz'
 with gzip.open(raw,'wt') as f:
  while True:
   page=c.analytics.query(spec=QuerySpec(source='token_viz',job_ids=[args.train],columns=[ColumnSpec(field=x) for x in ['step','payload','response_length','loss']],sort_by='step',sort_order='asc',limit=1024,offset=offset))
   for row in page.rows:
    payload=json.loads(row['payload']);key=(row['step'],payload['sample_index'],payload['segment_index'])
    if key in seen:continue
    seen.add(key);f.write(json.dumps({**row,'payload':payload})+'\n')
    result=arguments(payload);result.update(step=row['step'],sample_index=payload['sample_index'],prompt_target_sha256=hashlib.sha256((payload['student_prompt']+json.dumps(payload['sampled_token_ids'])).encode()).hexdigest());data.append(result)
   print(args.name,'downloaded',len(data),flush=True)
   if len(page.rows)<1024:break
   offset+=len(page.rows)
 steps=sorted({r['step'] for r in data});report={'train_id':args.train,'rows':len(data),'steps':{str(s):summarize([r for r in data if r['step']==s]) for s in steps},'windows':{f'{a}-{a+9}':summarize([r for r in data if a<=r['step']<a+10]) for a in [0,10,20,30]},'limitations':['Training batches differ by step; class balance reduces composition confounding but does not create fixed validation.','Tokens overlapping only actual argument letters/digits are counted; fixed protocol, tool name and parameter-name syntax are excluded.','Mean over action classes present in each window; rare raises may be missing from individual batches.','Training CE is not poker quality or proof of convergence.'],'raw_samples_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}
 (root/f'{args.name}-action-ce-rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in data))
 (root/f'{args.name}-action-ce.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'name':args.name,'steps':len(steps),'rows':len(data),'windows':report['windows']},indent=2))
if __name__=='__main__':main()
