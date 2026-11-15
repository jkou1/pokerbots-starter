"""CPU-only source eligibility/hints from original input, verified visible history."""
import json,re,gzip,hashlib,collections,sys
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'cleanup-multihand-rl20-v1'));from factual_filter import PATTERN,visible_fact_ledger,validate_contents
rows=[json.loads(l)for l in gzip.open(R/'raw/source-rows.jsonl.gz','rt')];groups=collections.defaultdict(list)
for row in rows:
 a=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];m=re.fullmatch(r'vals-arena/(m_[^/]+)/hand-(\d+)/seat(\d+)',a['conversation_id']);groups[(m[1],int(m[3]))].append(row)
ledgers={k:visible_fact_ledger(v)for k,v in groups.items()};contexts=[json.loads(l)for l in(R/'genuine-train-contexts.jsonl').open()];eligible=[];rejected=[];cards=re.compile(r'\b(?:[2-9TJQKA][cdhs]|10[cdhs])\b',re.I)
for c in contexts:
 items=json.loads(c['original_input_json_exact']);memory=next((re.search(r'<<<SCRATCHPAD\n(.*?)\nSCRATCHPAD>>>',x.get('content',''),re.S)[1]for x in items if x.get('role')=='user'and re.search(r'<<<SCRATCHPAD\n(.*?)\nSCRATCHPAD>>>',x.get('content',''),re.S)), '');current=c['hand'];ledger=ledgers[(c['source_match_id'],c['seat'])];reasons=[];prior=[]
 if current not in ledger:reasons.append('current canonical cleanup facts absent')
 matches=list(PATTERN.finditer(memory));residual=PATTERN.sub('',memory)
 if cards.search(residual):reasons.append('unparsed/unobservable card claim in incoming memory')
 for m in matches:
  n=int(m[1]);v=validate_contents(m.group(0),ledger,n)
  if n>=current:reasons.append('future/current hand claim in incoming prior memory')
  elif not v['accepted']:reasons.append('incoming card/stack claim not verified in own visible history')
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
 hint=('Teacher-only cleanup guidance. The student receives no hint. Call update_scratchpad exactly once with contents only, at most1200characters. Keep correct current-hand facts and at least one useful prior-hand stack-history fact already provided in the original input. Do not reset to current-only/empty notes. Never add unobserved opponent cards, future events, invented reads or facts. Prefer short structured summaries; do not copy the whole incoming scratchpad. Current facts literally supplied in the original input:\nFinal board: '+curboard[1]+'\nStacks now: '+curstacks[1]+'\nOne verified prior fact block already present verbatim in original incoming scratchpad (reference material, not a prewritten target):\n'+prior[0]['original_literal'])
 eligible.append({**c,'teacher_hint':hint,'hint_facts_all_literal_original_input':True,'verified_prior_fact_blocks':prior,'current_visible_source_span_id':fact['visible_source_span_id'],'status':'eligible_original_full_input_visible_facts_verified','off_policy_context_source':'incumbent C','intended_reply_sampler':'OWN10 ckpt_95bc5ed22ed8','canonical_tools_source':'/Users/lance/Documents/pokerbots-main/opsd/tools.json'})
# Round-robin whole TRAIN groups; no holdout reassignment or source repairs.
buckets=collections.defaultdict(list)
for c in eligible:buckets[c['source_match_id']].append(c)
for v in buckets.values():v.sort(key=lambda c:hashlib.sha256(c['span_id'].encode()).hexdigest())
selected=[]
while len(selected)<32 and any(buckets.values()):
 for k in sorted(buckets):
  if buckets[k]and len(selected)<32:selected.append(buckets[k].pop(0))
(R/'eligible-contexts.jsonl').write_text(''.join(json.dumps(c)+'\n'for c in eligible));(R/'selected32-contexts.jsonl').write_text(''.join(json.dumps(c)+'\n'for c in selected));(R/'source-reject-ledger.jsonl').write_text(''.join(json.dumps(c)+'\n'for c in rejected));report={'genuine_long_train':len(contexts),'eligible_visible_fact_long_train':len(eligible),'selected':len(selected),'eligible_matches':len({c['source_match_id']for c in eligible}),'selected_matches':len({c['source_match_id']for c in selected}),'reject_reasons':dict(collections.Counter(r for c in rejected for r in c['reasons'])),'no_model_calls':True,'source_prefixes_not_quoted_or_cleaned':True,'all_hint_facts_literal_original_input':True};(R/'eligibility-counts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
