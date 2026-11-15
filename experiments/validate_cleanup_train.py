import json,re,hashlib,collections
from pathlib import Path
ROOT=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/cleanup-own-train-v1');accepted=[];audit=[]
for f in sorted((ROOT/'traces').glob('*.json')):
 trace=json.loads(f.read_text());logpath=ROOT/'logs'/f.name;log=json.loads(logpath.read_text());seat='seat'+str(trace['policy_seat']);h=log['hands'][0];cleanup=log['private'][seat]['hands']['1']['cleanup']
 for i,span in enumerate(trace['spans']):
  out=json.loads(span['output']);calls=[x for x in out if x.get('type')=='function_call' and x.get('name')=='update_scratchpad']
  if len(calls)!=1:continue
  target=json.loads(calls[0]['arguments']);text=target.get('contents','');reasons=[]
  try:
   stacks=json.loads(re.search(r'stacks (\{.*?\})',text).group(1).replace('\\"','"'))
   if stacks!=log['final_stacks']:reasons.append('stack claims differ from recorded final stacks')
   board=re.search(r'board ([^;,]*)',text).group(1).strip();board=[] if board=='-' else board.split()
   if board!=h['final_board']:reasons.append('board claim differs from recorded final board')
   claims=collections.Counter(re.findall(r'(seat\d+) (preflop|flop|turn|river) (fold|check|call|bet|raise)',text));facts=collections.Counter((a['player'],a['street'],a['action']['type']) for a in h['actions'])
   if any(v>facts[k] for k,v in claims.items()):reasons.append('action claim absent from recorded hand')
  except Exception as e:reasons.append('unparsed factual summary: '+str(e))
  if len(text)>1500:reasons.append('over1500characters')
  if cleanup['result']!='updated' or not any(a.get('contents')==text and a.get('outcome')=='ok' for a in cleanup['attempts']):reasons.append('not an observed successful cleanup')
  audit.append({'seed':int(f.stem),'characters':len(text),'accepted':not reasons,'reasons':reasons})
  if reasons:continue
  accepted.append({'split':'train','tool':'update_scratchpad','target':target,'observed_input':json.loads(span['input']),'input_json_exact':span['input'],'observed_output':out,'provenance':{'kind':'actual_own_model_cleanup','model':trace['model'],'checkpoint':'ckpt_51eee61470f7','seed':int(f.stem),'policy_seat':trace['policy_seat'],'source_trace':str(f),'source_log':str(logpath),'span_index':i,'trace_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(span['input'].encode()).hexdigest()},'validation':{'successful_observed_cleanup':True,'exact_final_board':True,'exact_final_stacks':True,'all_action_claims_observed':True,'action_notes_not_claimed_chronological':True,'contents_characters':len(text)}})
(ROOT/'validated-train.jsonl').write_text('\n'.join(json.dumps(x) for x in accepted)+'\n');(ROOT/'validation.json').write_text(json.dumps({'accepted':len(accepted),'rejected':len(audit)-len(accepted),'audit':audit,'scope':'Only exact observed own replies; no target text changed or private notes invented.'},indent=2));print(json.dumps({'accepted':len(accepted),'audit':audit},indent=2))
