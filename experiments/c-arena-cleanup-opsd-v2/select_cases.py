"""CPU-only source eligibility/hints from original input, verified visible history."""
import json,re,gzip,hashlib,collections,sys
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parent/'c-arena-cleanup-opsd-v1';sys.path.insert(0,str(R.parent/'cleanup-multihand-rl20-v1'));from factual_filter import PATTERN,visible_fact_ledger,validate_contents
rows=[json.loads(l)for l in gzip.open(S/'raw/source-rows.jsonl.gz','rt')];groups=collections.defaultdict(list)
for row in rows:
 a=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];m=re.fullmatch(r'vals-arena/(m_[^/]+)/hand-(\d+)/seat(\d+)',a['conversation_id']);groups[(m[1],int(m[3]))].append(row)
ledgers={k:visible_fact_ledger(v)for k,v in groups.items()};contexts=[json.loads(l)for l in(S/'genuine-train-contexts.jsonl').open()];eligible=[];rejected=[];cards=re.compile(r'\b(?:[2-9TJQKA][cdhs]|10[cdhs])\b',re.I)
for c in contexts:
 items=json.loads(c['original_input_json_exact']);memory=next((re.search(r'<<<SCRATCHPAD\n(.*?)\nSCRATCHPAD>>>',x.get('content',''),re.S)[1]for x in items if x.get('role')=='user'and re.search(r'<<<SCRATCHPAD\n(.*?)\nSCRATCHPAD>>>',x.get('content',''),re.S)), '');current=c['hand'];ledger=ledgers[(c['source_match_id'],c['seat'])];reasons=[];prior=[]
 if current not in ledger:reasons.append('current canonical cleanup facts absent')
 matches=list(PATTERN.finditer(memory));residual=PATTERN.sub('',memory)
 if cards.search(residual):pass # Existing uncertain source prose is preserved, never promoted into hint facts
 for m in matches:
  n=int(m[1]);v=validate_contents(m.group(0),ledger,n)
  if n>=current or not v['accepted']:continue
  else:prior.append({'hand':n,'original_literal':m.group(0),'visible_source_span_id':ledger[n]['visible_source_span_id']})
 if not prior:reasons.append('no verified prior stack-history fact provided in original input')
 if any(x.get('type')not in ['message','function_call','function_call_output']for x in items):reasons.append('unsupported original runtime item type')
 for x in items:
  if x.get('type')=='function_call':
   try:assert isinstance(json.loads(x['arguments']),dict)
   except (ValueError,KeyError,AssertionError):reasons.append('unrenderable historical tool arguments')
 if reasons:rejected.append({'span_id':c['span_id'],'match_id':c['source_match_id'],'reasons':sorted(set(reasons))});continue
 fact=ledger[current];prior=sorted(prior,key=lambda x:x['hand'],reverse=True);last=next(x['content']for x in reversed(items)if x.get('role')=='user');curboard=re.search(r'^Final board:\s*(.*)$',last,re.M);curstacks=re.search(r'^Stacks now:\s*(.*)$',last,re.M)
 if not(curboard and curstacks):rejected.append({'span_id':c['span_id'],'match_id':c['source_match_id'],'reasons':['current facts not literally in original last user']});continue
 hint=('Teacher-only closed-world cleanup instruction. Call update_scratchpad exactly once with only contents. Target at most700characters, absolute acceptance limit1500. Retain current hand and at least one supplied prior hand. Contents must contain ONLY Hand N: board <cards or ->; stacks <JSON> factual summaries from the verified facts below. Do not include ANY actions, bets, folds, streets, showdown, hole cards, winners, pots, positions, reads, chat, quotes, SCRATCHPAD delimiters or other narrative. Do not copy old prose. No other facts are authorized. These verified facts are already present in the original input; this is reference material, not a prewritten output.\n'+json.dumps({'current':{'hand':current,'board':fact['final_board'],'stacks':fact['ending_stacks']},'prior':{'hand':prior[0]['hand'],'board':ledger[prior[0]['hand']]['final_board'],'stacks':ledger[prior[0]['hand']]['ending_stacks']}},sort_keys=True))
 eligible.append({**c,'teacher_hint':hint,'hint_facts_all_literal_original_input':True,'verified_prior_fact_blocks':prior,'current_visible_source_span_id':fact['visible_source_span_id'],'status':'eligible_original_full_input_visible_facts_verified','off_policy_context_source':'incumbent C','intended_reply_sampler':'OWN10 ckpt_95bc5ed22ed8','canonical_tools_source':'/Users/lance/Documents/pokerbots-main/opsd/tools.json'})
# Deterministic next eligible contexts, favoring source matches absent from V1.
old=[json.loads(l)for l in(S/'locked-first10-contexts.jsonl').open()];oldids={c['span_id']for c in old};oldmatches={c['source_match_id']for c in old};eligible=[c for c in eligible if c['span_id']not in oldids];buckets=collections.defaultdict(list)
for c in eligible:buckets[c['source_match_id']].append(c)
for v in buckets.values():v.sort(key=lambda c:hashlib.sha256(c['span_id'].encode()).hexdigest())
keys=sorted(buckets,key=lambda k:(k in oldmatches,k));selected=[]
while len(selected)<10 and any(buckets.values()):
 for k in keys:
  if buckets[k]and len(selected)<10:selected.append(buckets[k].pop(0))
assert len(selected)==10
(R/'locked-first10-contexts.jsonl').write_text(''.join(json.dumps(c)+'\n'for c in selected));report={'genuine_source_train_long':len(contexts),'eligible_unused_contexts':len(eligible),'selected':len(selected),'selected_matches':len({c['source_match_id']for c in selected}),'new_matches_vs_v1':len({c['source_match_id']for c in selected}-oldmatches),'overlap_span_ids':0,'source_contexts_unmodified':True,'specific_hint_facts_verified_original_visible_ledger':True,'teacher_hint_closed_world_board_stacks_only':True,'no_model_calls':True};(R/'source-counts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
