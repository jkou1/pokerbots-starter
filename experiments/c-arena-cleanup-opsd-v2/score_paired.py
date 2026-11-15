import json,gzip,re,sys,collections
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'cleanup-multihand-rl20-v1'));from factual_filter import validate_contents,visible_fact_ledger
rows=[json.loads(l)for l in gzip.open(R.parent/'c-arena-cleanup-opsd-v1/raw/source-rows.jsonl.gz','rt')];groups=collections.defaultdict(list)
for row in rows:
 a=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];m=re.fullmatch(r'vals-arena/(m_[^/]+)/hand-(\d+)/seat(\d+)',a['conversation_id']);groups[(m[1],int(m[3]))].append(row)
contexts=[json.loads(l)for l in(R/'locked-first10-contexts.jsonl').open()];results=json.loads((R/'raw/paired-first10-results.json').read_text())['results'];scores=[]
for i,(c,result)in enumerate(zip(contexts,results)):
 ledger=visible_fact_ledger(groups[(c['source_match_id'],c['seat'])]);record={'case':i+1,'arms':{}}
 for arm,v in result['arms'].items():
  errors=[];calls=v.get('tool_calls',[]);contents=''
  try:
   assert len(calls)==1 and calls[0]['function']['name']=='update_scratchpad';args=json.loads(calls[0]['function']['arguments']);assert set(args)=={'contents'} and isinstance(args['contents'],str);contents=args['contents']
  except Exception:errors.append('not exactly one contents-only update_scratchpad')
  if not 0<len(contents)<=1500:errors.append('length outside1..1500')
  if v.get('truncated')is not False:errors.append('truncation/error')
  facts=validate_contents(contents,ledger,c['hand']);errors+=facts['errors'];prior=set(x['hand']for x in c['verified_prior_fact_blocks'])&set(facts.get('claimed_hand_numbers',[]))
  if not prior:errors.append('no provided verified prior fact retained')
  record['arms'][arm]={'useful_valid':not errors,'characters':len(contents),'errors':sorted(set(errors)),'fact_blocks':facts.get('claims',0),'provided_prior_facts_retained':sorted(prior)}
 scores.append(record)
counts={arm:sum(x['arms'][arm]['useful_valid']for x in scores)for arm in ['unhinted','hinted']};out={'cases_intention_to_treat':10,'logical_calls':20,'counts':counts,'gain':counts['hinted']-counts['unhinted'],'gate_pass':counts['hinted']>=8 and counts['hinted']-counts['unhinted']>=3,'factual_scope':'Conservative all-claims validation; unparsed residual claims quarantined, not accepted','finish_metadata_recovery_pending':True,'cases':scores};(R/'paired-first10-score.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
