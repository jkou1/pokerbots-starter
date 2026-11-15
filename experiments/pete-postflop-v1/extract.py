"""Extract legal, flag-clean Pete decisions with original match/deal holdouts."""
import hashlib,json,sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.pete import PETE,BAD_FLAGS,ADAPTER,replay_hand,deal_identity,split_for
from poker_harness.completions import table_rules,with_preset
from poker_harness.prompts import system_prompt,decision_prompt
ROOT=Path(__file__).resolve().parent

def main():
 rows={s:[] for s in ['train','select','eval']};pre={s:[] for s in rows};seen=set();bad={};counts=Counter();sources=[]
 for p in sorted((ROOT/'raw').glob('*.json')):
  m=json.loads(p.read_bytes());identity=deal_identity(m)
  if identity in seen:counts['duplicate_deals']+=1;continue
  try:
   pete={s['seat'] for s in m['seats'] if s['entry']['id']==PETE}
   if not pete:raise ValueError('No Pete seat')
   rules=table_rules(with_preset({'preset':'event','total_hands':m['format']['total_hands'],'seats':len(m['seats'])}))
   current=[]
   for hand in m['hands']:
    for index,ctx,target,source in replay_hand(m,hand):
     if ctx.seat not in pete:continue
     args=source.get('tool_args') or {}
     if any(source.get(k) for k in BAD_FLAGS) or any(args.get(k)!=v for k,v in target.items()):counts['flagged_targets']+=1;continue
     current.append({'input':[{'role':'system','content':system_prompt(rules)},{'role':'user','content':decision_prompt(ctx,talk=False)}],'target':target,'provenance':{'match_id':m['id'],'hand':hand['hand_number'],'action_index':index,'seat':ctx.seat,'street':ctx.street,'adapter':ADAPTER,'teacher':PETE,'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'legal':asdict(ctx.legal),'position':ctx.position,'hole_cards':ctx.hole_cards,'observation_kind':'reconstructed_without_private_memory','split':split_for(identity),'deal_identity':identity})
   seen.add(identity)
   for r in current:
    (pre if r['provenance']['street']=='preflop' else rows)[r['split']].append(r)
    counts[f"{r['split']}:{r['provenance']['street']}:{r['target']['action']}"]+=1
   sources.append({'file':p.name,'deal_identity':identity,'split':split_for(identity),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  except Exception as e:bad[p.name]=f'{type(e).__name__}: {e}'
 for split in rows:
  (ROOT/f'{split}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows[split]))
  (ROOT/f'preflop-{split}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in pre[split]))
 manifest={'replay_valid_matches':len(sources),'quarantined':bad,'counts':dict(counts),'postflop_splits':{s:len(v) for s,v in rows.items()},'preflop_splits':{s:len(v) for s,v in pre.items()},'sources':sources,'limitations':['No private memory or original teacher reasoning is available.','Teacher outcomes do not prove optimal actions.','Reconstruction omits public incoming chatter consistently with original exporter.']}
 manifest['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*train.jsonl')}
 (ROOT/'quality.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k!='sources'},indent=2))
if __name__=='__main__':main()
