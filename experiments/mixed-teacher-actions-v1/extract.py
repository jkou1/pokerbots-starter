"""Replay teachers' own states; split whole matches/duplicate deals before mixing."""
import hashlib,json,random,sys
from collections import Counter,defaultdict
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.pete import BAD_FLAGS,replay_hand
from poker_harness.completions import table_rules,with_preset
from poker_harness.prompts import system_prompt,decision_prompt
ROOT=Path(__file__).resolve().parent
TEACHERS=['house-professor-pete','house-chatty-carlos']
sha=lambda x:hashlib.sha256(x.encode()).hexdigest()
class Union:
 def __init__(self,keys):self.p={k:k for k in keys}
 def find(self,x):
  while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
  return x
 def join(self,a,b):
  a,b=self.find(a),self.find(b)
  if a!=b:self.p[max(a,b)]=min(a,b)
def deal_id(hand):
 # Conservative card-deal identity: exact dealt private cards at each seat and
 # button, independent of action outcomes/stacks/teacher. Used only for grouping.
 return sha(json.dumps([hand['button_seat'],sorted((p['seat'],sorted(p['hole_cards'])) for p in hand['players'])],sort_keys=True))
def source_ids(path):
 return {json.loads(l)['provenance']['match_id'] for l in path.open()} if path.exists() else set()
def main():
 manifests={r['id']:r for r in map(json.loads,(ROOT/'manifest.jsonl').open()) if r['result']=='complete'}
 matches={ident:json.loads((ROOT/'raw'/f'{ident}.json').read_bytes()) for ident in manifests}
 union=Union(matches);deals={};duplicate_edges=[]
 for ident,m in matches.items():
  for h in m['hands']:
   key=deal_id(h)
   if key in deals and deals[key]!=ident:union.join(ident,deals[key]);duplicate_edges.append({'a':ident,'b':deals[key],'deal_sha256':key})
   else:deals[key]=ident
 components=defaultdict(list)
 for ident in matches:components[union.find(ident)].append(ident)
 legacy=ROOT.parent/'pete-postflop-v1';protected={s:set().union(*(source_ids(legacy/f'{prefix}{s}.jsonl') for prefix in ['','preflop-'])) for s in ['select','eval']}
 groups={};match_group={};conflicts=[]
 for members in components.values():
  members=sorted(members);key=sha('|'.join(members));bucket=int(key[:16],16)%100;split='train' if bucket<80 else 'select' if bucket<90 else 'eval';reason='whole-match-group hash'
  if set(members)&protected['eval']:
   split='eval';reason='preserve frozen legacy final source group'
   if set(members)&protected['select']:conflicts.append(key)
  elif set(members)&protected['select']:split='select';reason='preserve frozen legacy selection source group'
  groups[key]={'match_ids':members,'split':split,'reason':reason}
  for ident in members:match_group[ident]=key
 allrows={s:[] for s in ['train','select','eval']};bad={};seen=set();counts=Counter();teacher_matches=defaultdict(set);fullgame_replayed=0
 for ident,m in sorted(matches.items()):
  group=match_group[ident];split=groups[group]['split'];rows=[]
  try:
   if m.get('schema')!='vals-arena.match/1' or m.get('runner_version')!='0.1.0' or m.get('status')!='complete':raise ValueError('Unsupported source contract')
   if (m['format']['small_blind'],m['format']['big_blind'],m['format']['total_hands'],len(m['seats']))!=(1,2,30,6):raise ValueError('Non-official format contract')
   seat_teacher={s['seat']:s['entry']['id'] for s in m['seats'] if s['entry']['id'] in TEACHERS}
   if not seat_teacher:raise ValueError('No canonical teacher seat')
   rules=table_rules(with_preset({'preset':'event','total_hands':m['format']['total_hands'],'seats':len(m['seats'])}))
   for hand in m['hands']:
    for index,ctx,target,source in replay_hand(m,hand):
     teacher=seat_teacher.get(ctx.seat)
     if not teacher:continue
     counts[f'{teacher}:seen']+=1;args=source.get('tool_args') or {}
     if isinstance(args,str):args=json.loads(args)
     if any(source.get(k) for k in BAD_FLAGS) or any(args.get(k)!=v for k,v in target.items()):counts[f'{teacher}:rejected_flag_or_target']+=1;continue
     key=(ident,hand['hand_number'],index,teacher)
     if key in seen:raise ValueError('Duplicate source decision')
     seen.add(key)
     rows.append({'input':[{'role':'system','content':system_prompt(rules)},{'role':'user','content':decision_prompt(ctx,talk=True)}],'target':target,'tool':'submit_action','split':split,'provenance':{'teacher':teacher,'match_id':ident,'hand':hand['hand_number'],'action_index':index,'seat':ctx.seat,'street':ctx.street,'source_group':group,'private_card_deal_sha256':deal_id(hand),'raw_url':manifests[ident]['raw_url'],'raw_sha256':manifests[ident]['sha256'],'adapter':'mixed-public-prefix-replay-v1'},'legal':asdict(ctx.legal),'position':ctx.position,'hole_cards':ctx.hole_cards,'observation_kind':'reconstructed_decision_time_state_with_public_current_hand_chatter_without_private_memory','target_fields':['action','amount'] if 'amount' in target else ['action']})
   fullgame_replayed+=1;allrows[split]+=rows
   for r in rows:
    teacher=r['provenance']['teacher'];teacher_matches[teacher].add(ident);counts[f'{split}:{teacher}:{r["provenance"]["street"]}:{r["target"]["action"]}']+=1
  except Exception as e:bad[ident]=f'{type(e).__name__}: {e}'
 # Balance teachers by UNIQUE examples; preserve each teacher's original
 # street/action frequencies via largest-remainder proportional sampling.
 by_teacher={t:[r for r in allrows['train'] if r['provenance']['teacher']==t] for t in TEACHERS};size=min(map(len,by_teacher.values()));selected=[];balance={}
 for teacher,rows in by_teacher.items():
  strata=defaultdict(list)
  for r in rows:strata[(r['provenance']['street'],r['target']['action'])].append(r)
  exact={k:len(v)*size/len(rows) for k,v in strata.items()};allocation={k:int(v) for k,v in exact.items()}
  for k in sorted(exact,key=lambda k:(-(exact[k]-allocation[k]),k))[:size-sum(allocation.values())]:allocation[k]+=1
  teacher_selected=[]
  for k,v in sorted(strata.items()):random.Random(42).shuffle(v);teacher_selected+=v[:allocation[k]]
  assert len(teacher_selected)==size;selected+=teacher_selected
  balance[teacher]={'available_unique_train':len(rows),'selected_unique_train':len(teacher_selected),'available_by_street_action':{f'{k[0]}:{k[1]}':len(v) for k,v in sorted(strata.items())},'selected_by_street_action':{f'{k[0]}:{k[1]}':allocation[k] for k in sorted(allocation)},'unique_source_matches':len({r['provenance']['match_id'] for r in teacher_selected})}
 random.Random(42).shuffle(selected)
 for split,rows in allrows.items():
  (ROOT/f'unbalanced-{split}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
  if split=='train':rows=selected
  (ROOT/f'{split}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 split_matches={s:{r['provenance']['match_id'] for r in rows} for s,rows in allrows.items()};split_groups={s:{r['provenance']['source_group'] for r in rows} for s,rows in allrows.items()}
 for a,b in [('train','select'),('train','eval'),('select','eval')]:assert not split_matches[a]&split_matches[b] and not split_groups[a]&split_groups[b]
 assert not split_matches['train']&(protected['select']|protected['eval'])
 quality={'canonical_teachers':TEACHERS,'replay_valid_matches':fullgame_replayed,'quarantined':bad,'source_match_count':len(matches),'whole_match_groups':len(groups),'duplicate_deal_edges':duplicate_edges,'frozen_legacy_protection':{s:sorted(v) for s,v in protected.items()},'legacy_selection_final_component_conflicts':conflicts,'source_groups':groups,'balance':balance,'splits':{'train':len(selected),'select':len(allrows['select']),'eval':len(allrows['eval'])},'counts':dict(counts),'target_format':'qwen-protocol-boundary-v2','teacher_identity_only_in_provenance':True,'no_say_targets':True,'no_cleanup_targets':True,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.jsonl') if p.name!='manifest.jsonl'}}
 (ROOT/'quality.json').write_text(json.dumps(quality,indent=2)+'\n')
 print(json.dumps({k:v for k,v in quality.items() if k not in ['source_groups','counts','frozen_legacy_protection','duplicate_deal_edges','sha256']},indent=2))
if __name__=='__main__':main()
