"""Freeze sixteen consistent TRAIN states and teacher-only action/fact hints; no calls."""
import json,re,hashlib,collections,sys
from pathlib import Path
from pokerkit import Card,StandardHighHand
R=Path(__file__).resolve().parent;V=R.parent/'pokerbench-v4';sys.path.insert(0,str(R.parent/'pokerbench-v3'));from audit import ACTION,audit
sha=lambda b:hashlib.sha256(b).hexdigest()
if(R/'manifest.json').exists():raise SystemExit('Frozen calibration already exists; no output-dependent case/hint changes')
RANK={'ace':'A','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'T','jack':'J','queen':'Q','king':'K'};SUIT={'club':'c','diamond':'d','heart':'h','spade':'s'};CARD=re.compile(r'\b(Ace|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Jack|Queen|King)\s+Of\s+(Club|Diamond|Heart|Spade)s?\b',re.I)
def cards(text):return[RANK[a.lower()]+SUIT[b.lower()]for a,b in CARD.findall(text)]
def category(holes,board):return StandardHighHand.from_game(tuple(Card.parse(''.join(holes))),tuple(Card.parse(''.join(board)))).entry.label.value
assert category(['2h','4h'],['6h','8h','Th','3c','5s'])=='Flush' # straight+flush acrossdifferentcards is NOT straightflush
assert category(['Ad','Kd'],['Qd','Jd','Td','2c','3s'])=='Straight flush'
assert category(['As','Ad'],['Kc','Qh','Js'])=='One pair'
def state(row):
 text=row['input'][1]['content'];holdings=re.findall(r'your holding is \[([^\]]+)\]',text,re.I);assert holdings and len({tuple(cards(x))for x in holdings})==1;hole=cards(holdings[0]);assert len(hole)==2;board=[]
 for street,n in [('flop',3),('turn',1),('river',1)]:
  m=re.search(r'The '+street+r' comes(.*?)(?:,?\s+then\b)',text,re.I|re.S)
  if m:found=cards(m[1]);assert len(found)==n;board+=found
 assert len(board)in[3,4,5]and len(set(hole+board))==len(hole+board);seats=['UTG','HJ','CO','BTN','SB','BB'];st={s:200 for s in seats};be={s:0 for s in seats};be['SB']=1;be['BB']=2;st['SB']-=1;st['BB']-=2;hero=re.search(r'your position is (UTG|HJ|CO|BTN|SB|BB)',text)[1];last=2
 for n,part in enumerate(re.split(r'The flop comes|The turn comes|The river comes',text)):
  if n:be={s:0 for s in seats}
  last=2
  for seat,action,num in ACTION.findall(part):
   old=max(be.values())
   if action in ['bet','raise']:
    total=int(num);commit=total-be[seat]
    if total-old>=last:last=total-old
   elif action=='call':commit=min(st[seat],old-be[seat])
   else:continue
   assert 0<=commit<=st[seat];st[seat]-=commit;be[seat]+=commit
 pot=int(re.search(r'current pot size is (\d+) chips',text)[1]);assert pot==1200-sum(st.values())and st[hero]>0;assert audit(row)=='passed';call=min(st[hero],max(be.values())-be[hero]);legal={'can_fold':True,'can_check':call==0,'call_amount':call,'raise_type':'raise'if max(be.values())else'bet','min_raise_to':min(st[hero]+be[hero],max(be.values())+last),'max_raise_to':st[hero]+be[hero]};return{'hero_cards_visible':hole,'current_board_visible':board,'hero_best_five_category':category(hole,board),'pot_chips':pot,'to_call_chips':call,'legal':legal,'position':hero,'hero_remaining_stack_derived':st[hero]}
rows=[json.loads(l)for l in(V/'train.jsonl').open()];buckets=collections.defaultdict(list);rejected=collections.Counter()
for row in rows:
 try:facts=state(row)
 except Exception as e:rejected[type(e).__name__]+=1;continue
 assert row['split']=='train'and'pot_reconciliation'not in row['provenance'];buckets[row['target']['action']].append((row,facts))
for v in buckets.values():v.sort(key=lambda x:sha(('strategy-opsd-v1|'+x[0]['provenance']['source_sha256']).encode()))
need={'bet':4,'raise':4,'call':4,'fold':2,'check':2};groups=set();selected=[]
for action,n in need.items():
 for row,facts in buckets[action]:
  group=row['provenance']['scenario_group']
  if group in groups:continue
  target=row['target'];facthint={k:facts[k]for k in ['hero_best_five_category','pot_chips','to_call_chips']};hint=('TEACHER-ONLY strategy calibration reference. The normal student does not receive this reference. Quoted provider demonstration action: '+json.dumps(target,sort_keys=True)+'. Any bet/raise amount is a street-total chip amount. This is an attributed benchmark-provider label, not independently proven optimality or private provider reasoning. Verified facts derived only from the original visible own cards/current board and decision-time history: '+json.dumps(facthint,sort_keys=True)+'. Use this privileged reference when reasoning through the spot, then make exactly one genuine submit_action call. Do not add hidden opponent cards or future information.');selected.append({'case':len(selected),'split':'train','original_input':row['input'],'original_input_sha256':sha(json.dumps(row['input'],sort_keys=True).encode()),'original_provider_scaled_target':target,'source_provenance':row['provenance'],'facts':facts,'teacher_system_only_hint':hint,'teacher_hint_sha256':sha(hint.encode()),'target_optimality_not_independently_verified':True});groups.add(group);n-=1
  if n==0:break
 assert n==0
assert len(selected)==16 and len(groups)==16
(R/'cases.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n'for x in selected));manifest={'stage':'CPUfrozen,no modelcalls/upload/train','source':str(V/'train.jsonl'),'source_sha256':sha((V/'train.jsonl').read_bytes()),'consistent_train_only':True,'reconciled_select_final_cases':0,'cases':16,'distinct_original_scenario_groups':16,'action_counts':dict(collections.Counter(x['original_provider_scaled_target']['action']for x in selected)),'cards_verified_by':'PokerKit StandardHighHand.from_game,ownholecards+currentboard only;3focusedknownfixturespassinclstraight+flushnotstraightflush','teacher_hint_only_system_mutation':True,'student_normal_P_unchanged':True,'no_fabricated_provider_reasoning':True,'canonical_tools_sha256':sha(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_bytes()),'cases_sha256':sha((R/'cases.jsonl').read_bytes()),'prospective_probe':{'model':'catalogQwen/Qwen3.6-35B-A3B,notSFTcheckpoint','pairs':16,'logical_calls':32,'temperature_both':1,'max_completion_tokens_both':5000,'retries':0,'separate_ephemeral_GPU':1,'requires_eval_READY_and_root32callGO':True},'frozen_gate':{'hinted_exact_action_amount_min':14,'paired_case_gain_min':4,'all16_hinted_genuine_single_correct_tool_legal_not_truncated':True,'fail_closes_without_native_training':True},'native_training_GO':False};(R/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
