"""Validate genuine own cleanup targets and serialize prior runtime history safely."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.training import supervised_task
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/cleanup-own-train-v1/validated-train.jsonl')
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[];checks=[]
for line in SOURCE.open():
 original=json.loads(line);v=original['validation'];provenance=original['provenance'];observed=original['observed_input'];target=original['target']
 assert original['split']=='train' and original['tool']=='update_scratchpad'
 assert all(v[k] for k in ['successful_observed_cleanup','exact_final_board','exact_final_stacks','all_action_claims_observed'])
 assert 0<len(target['contents'])<=1500
 assert provenance['kind']=='actual_own_model_cleanup'
 assert sha(Path(provenance['source_trace']).read_bytes())==provenance['trace_sha256']
 assert observed[-1]['type']=='message' and observed[-1]['role']=='user' and 'Now call update_scratchpad' in observed[-1]['content']
 messages=[]
 for item in observed:
  if item['type']=='message' and item['role'] in ['system','user']:
   messages.append({'role':item['role'],'content':item['content']})
  else:
   messages.append({'role':'user','content':'Recorded prior own conversation item (context, not a new request):\n'+json.dumps(item,sort_keys=True)})
 row={'split':'train','tool':'update_scratchpad','input':messages,'target':target,'provenance':{**provenance,'adapter':'actual-own-history-quoted-user-context-v1','observation_kind':'observed_runtime_history_with_prior_own_assistant_tool_items_serialized_as_user_context','original_input_sha256':provenance['input_sha256'],'validated_source_sha256':sha(SOURCE.read_bytes())}}
 supervised_task(row)
 rows.append(row);checks.append({'seed':provenance['seed'],'source_trace_sha256':provenance['trace_sha256'],'input_source_sha256':provenance['input_sha256'],'contents_characters':len(target['contents']),'target_unchanged':row['target']==original['target'],'facts_validated':True})
(ROOT/'train.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
(ROOT/'train-tasks.jsonl').write_text(''.join(supervised_task(r).model_dump_json()+'\n' for r in rows))
manifest={'source':str(SOURCE),'source_sha256':sha(SOURCE.read_bytes()),'records':len(rows),'checks':checks,'no_generated_private_notes':True,'no_selection_inputs':True,'no_upload_or_training':True,'input_representation_changed':True,'limitations':['Only four unique short after-hand targets.','Prior own assistant/tool items are explicitly quoted as user context to avoid supervising historical replies.','One-hand TRAIN collection does not establish useful cross-hand memory.']}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
