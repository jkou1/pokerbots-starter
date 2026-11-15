"""CPU-only audit of recorded board/stack memory claims; never creates training labels."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent/'data/experiments';dev=json.loads((ROOT/'base20-development-v1/receipt.json').read_text());functional=json.loads((ROOT/'fullschema-functional30/rl20/receipt.json').read_text());files=[(p,'seat'+str(dev['seeds'].index(json.loads(p.read_text())['session_info']['seed'])))for p in (ROOT/'base20-development-v1/rl20/raw').glob('*.json')];files +=[(p,'seat'+str(functional['policy_seat']))for p in (ROOT/'fullschema-functional30/rl20/raw').glob('*.json')]
pattern=re.compile(r'hand\s+(\d+)\s*:\s*board\s+([^;,\n]*?)[;,]\s*stacks\s*(\{.*?\})',re.I);rows=[]
for path,seat in files:
 log=json.loads(path.read_text());hands={int(h['hand_number']):h for h in log['hands']}
 for number,entry in log['private'][seat]['hands'].items():
  cleanup=entry.get('cleanup',{});attempts=cleanup.get('attempts',[])
  if cleanup.get('result')!='updated' or not attempts:continue
  text=attempts[-1].get('contents','');matches=list(pattern.finditer(text));failures=[];parsed=0;current=False
  for match in matches:
   n=int(match[1]);current=current or n==int(number)
   if n>int(number) or n not in hands:failures.append({'claimed_hand':n,'reason':'future or nonexistent hand'});continue
   try:stacks=json.loads(match[3].replace('\\"','"'))
   except (ValueError,TypeError):failures.append({'claimed_hand':n,'reason':'unparsed stack JSON'});continue
   board=[] if match[2].strip()=='-' else match[2].strip().split();truth=hands[n];parsed+=1
   if [x.lower()for x in board]!=[x.lower()for x in truth['final_board']]:failures.append({'claimed_hand':n,'reason':'board mismatch','claimed':board,'recorded':truth['final_board'],'same_cards_ignoring_order':sorted(x.lower()for x in board)==sorted(x.lower()for x in truth['final_board'])})
   if stacks!=truth['ending_stacks']:failures.append({'claimed_hand':n,'reason':'stack mismatch','claimed':stacks,'recorded':truth['ending_stacks']})
  rows.append({'seed':log['session_info']['seed'],'seat':seat,'cleanup_hand':int(number),'recognized_board_stack_claims':parsed,'includes_current_hand_claim':current,'failures':failures,'source':str(path)})
unique={}
for row in rows:
 for failure in row['failures']:
  key=(row['seed'],failure['claimed_hand'],failure['reason'],json.dumps(failure.get('claimed'),sort_keys=True));unique[key]=failure
semantic=lambda f:not f.get('same_cards_ignoring_order',False)
report={'distinct_mismatch_types':len(unique),'current_hand_updates_with_semantic_mismatch':sum(any(f['claimed_hand']==row['cleanup_hand'] and semantic(f) for f in row['failures'])for row in rows),'updates_with_semantic_mismatch':sum(any(semantic(f)for f in row['failures'])for row in rows),'distinct_failures':[{'seed':key[0],**failure}for key,failure in unique.items()],'scope':'Partial factual audit only of recognizable hand/board/stacks claims in exact accepted own cleanup contents from4selection games+1functional game. No targets rewritten, no student inputs constructed, no training use, no final outcomes used. Unrecognized prose/action/opponent/range claims are not validated.','accepted_updates':len(rows),'recognized_claims':sum(x['recognized_board_stack_claims']for x in rows),'updates_with_no_recognized_claims':sum(not x['recognized_board_stack_claims']for x in rows),'updates_without_current_hand_claim':sum(not x['includes_current_hand_claim']for x in rows),'updates_with_detected_mismatch_or_parse_failure':sum(bool(x['failures'])for x in rows),'rows':rows};(ROOT/'rl20-cleanup-factual-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
