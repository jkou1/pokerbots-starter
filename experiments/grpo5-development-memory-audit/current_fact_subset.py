"""Deterministic subset check of explicit current-hand claims; free prose stays unknown."""
import json,gzip,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent;rows=[];private=[];card=r'[2-9TJQKA][cdhs]'
for s in map(json.loads,gzip.open(R/'raw/parent5-visible-spans.jsonl.gz','rt')):
 u=[x['content']for x in json.loads(s['input'])if x.get('role')=='user'];last=u[-1];m=re.match(r'^## Hand (\d+) is over',last)
 if not m or int(m[1])not in[5,10,20,25,30]:continue
 n=int(m[1]);decisions=[x for x in u if x.startswith(f'## Hand {n} of')];d=decisions[0]if decisions else'';pm=re.search(r'Your seat: \d+ \(position (\d+)',d);pos=int(pm[1])if pm else None;own=re.search(r'Your hole cards:\s*('+card+r')\s+('+card+')',d);own=set(own.groups())if own else None;calls=[x for x in json.loads(s['output'])if x.get('type')=='function_call'];note=json.loads(calls[0]['arguments'])['contents'];lines=note.splitlines();header=next((i for i,x in enumerate(lines)if re.match(rf'^Hand\s+{n}\s+Summary',x,re.I)),None);section=[]
 if header is not None:
  for l in lines[header+1:]:
   if not l.strip()and section:break
   if l.strip():section.append(l)
 # Restrict identity/position claims to own-agent wording in the current summary.
 ownlines=[l for l in section if re.search(r'\b(?:I had|I folded|Folded|SB with|BB with|BTN with)\b',l,re.I)]
 position=[];cards=[]
 for line in ownlines:
  p=re.search(r'\b(SB|BB) with\b|\b(?:from|in) (SB|BB)\b',line)
  if p:
   claimed=next(x for x in p.groups()if x);correct=((claimed=='SB'and pos==0)or(claimed=='BB'and pos==1))if pos is not None else None;position.append({'claim':claimed,'original_position':pos,'correct':correct})
  c=re.search(r'(?:with|I had|I folded|Folded)\s+('+card+r')\s*('+card+')',line,re.I)
  if c:cards.append({'correct':set(c.groups())==own if own is not None else None})
 stack_line=next((l for l in lines if re.search(r'(?:Updated\s+)?Stacks(?:\s+after\s+H\d+)?\s*:',l,re.I)),None);stackchecks=[]
 if stack_line:
  pairs=re.findall(r'\b(?:seat|S)(\d)(?:\(me\))?\s*(?:=|\s)\s*(\d+)',stack_line,re.I);truth=dict((k,int(v))for k,v in re.findall(r'seat(\d+)\s+(\d+)',re.search(r'^Stacks now:.*$',last,re.M)[0]));stackchecks=[{'seat':int(k),'correct':truth.get(k)==int(v)}for k,v in pairs]
 row={'trace_id':s['trace_id'],'span_id':s['span_id'],'hand':n,'input_sha256':hashlib.sha256(s['input'].encode()).hexdigest(),'output_sha256':hashlib.sha256(s['output'].encode()).hexdigest(),'own_current_position_claims':position,'own_current_hole_card_claims':cards,'current_stack_values':stackchecks,'current_summary_header_found':header is not None};rows.append(row);private.append({'record':row,'own_current_claim_lines':ownlines,'original_decision_seat':re.search(r'^Your seat:.*$',d,re.M)[0]if d else None,'original_holecards':re.search(r'^Your hole cards:.*$',d,re.M)[0]if d else None,'current_stacks_note_line':stack_line,'original_cleanup_stack_line':re.search(r'^Stacks now:.*$',last,re.M)[0]})
summary={'notes':len(rows),'position_claims_checked':sum(v['correct']is not None for x in rows for v in x['own_current_position_claims']),'notes_with_definite_current_position_error':sum(any(v['correct']is False for v in x['own_current_position_claims'])for x in rows),'own_hole_card_claims_checked':sum(v['correct']is not None for x in rows for v in x['own_current_hole_card_claims']),'notes_with_definite_own_hole_card_error':sum(any(v['correct']is False for v in x['own_current_hole_card_claims'])for x in rows),'explicit_current_stack_values_checked':sum(len(x['current_stack_values'])for x in rows),'incorrect_current_stack_values':sum(not v['correct']for x in rows for v in x['current_stack_values']),'notes_with_checked_stack_values':sum(bool(x['current_stack_values'])for x in rows),'scope':'Only regex-supported explicit OWN claims in current HandN Summary and explicit stack line. Unknown prose not accepted as factual; no broad quality or prior-memory claim.','no_hidden_raw_state_or_scratchpad_truth':True,'no_model_calls':True,'records':rows}
(R/'current-fact-subset.json').write_text(json.dumps(summary,indent=2)+'\n');(R/'raw/current-fact-subset-exact-evidence.json').write_text(json.dumps(private,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k!='records'},indent=2))
