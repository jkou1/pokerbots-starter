"""Replay captured API envelopes through the proven Completion parser; zero new calls."""
import json,sys
from pathlib import Path
from poker_harness.seat import Completion
from poker_harness.training import action_args,betting_action
from vals_tools.pete_eval import legal_prediction
from vals_tools.collect_policy import trace_reply
R=Path(__file__).resolve().parent;state=json.loads((R/'raw/results.json').read_text());assert state['status']=='complete';rows=[json.loads(l)for l in(R/'cases.jsonl').open()]
for row,record in zip(rows,state['results']):
 for arm in ['unhinted','hinted']:
  f=R/f"raw/case{row['case']}-{arm}-response.json";w=json.loads(f.read_text());choice=w['choices'][0];m=choice['message'];usage=w.get('usage')or{};calls=[{'id':c['id'],'type':'function','function':{'name':c['function']['name'],'arguments':c['function']['arguments']}}for c in m.get('tool_calls')or[]];reasoning=m.get('reasoning_content')or m.get('reasoning');reply=Completion(text=m.get('content')or'',reasoning=reasoning if isinstance(reasoning,str)else'',tool_arguments=None,tool_calls=calls,in_tokens=usage.get('prompt_tokens'),out_tokens=usage.get('completion_tokens'),reasoning_tokens=(usage.get('completion_tokens_details')or{}).get('reasoning_tokens'),truncated=choice.get('finish_reason')=='length')
  old=record['arms'][arm];v={'runtime_reply_exact':[x.model_dump(mode='json',exclude_none=True)for x in trace_reply(reply)],'reasoning':reply.reasoning,'text':reply.text,'tool_calls':reply.tool_calls,'legal':False,'exact_provider_action_amount':False,'truncated':reply.truncated,'finish_reason':choice.get('finish_reason'),'genuine_single_correct_tool':len(calls)==1 and calls[0]['function']['name']=='submit_action','complete':not reply.truncated and choice.get('finish_reason')in['tool_calls','stop'],'out_tokens':reply.out_tokens,'usage':usage,'response_id':w.get('id'),'seconds':old.get('seconds'),'scored_from_exact_saved_envelope':True}
  try:
   raw=action_args(reply);a=betting_action(raw);legal=bool(legal_prediction({'legal':row['facts']['legal']},a));v.update(raw_arguments=raw,normalized_action=a,legal=legal,exact_provider_action_amount=legal and a==row['original_provider_scaled_target'])
  except Exception as e:v['protocol_or_parse_error']=type(e).__name__+':'+str(e)[:300]
  record['arms'][arm]=v
(R/'raw/results-scored.json').write_text(json.dumps(state,indent=2)+'\n')
counts={a:sum(x['arms'][a]['exact_provider_action_amount']for x in state['results'])for a in['unhinted','hinted']};valid={a:sum(x['arms'][a]['legal']and x['arms'][a]['genuine_single_correct_tool']and x['arms'][a]['complete']for x in state['results'])for a in['unhinted','hinted']};s={'cases_intention_to_treat':16,'logical_calls':32,'model':'infer_aea1a2390d3d','catalog_model':'Qwen/Qwen3.6-35B-A3B','version':1,'counts_exact_normalized_action_amount':counts,'counts_genuine_legal_complete':valid,'gain':counts['hinted']-counts['unhinted'],'all16_hinted_genuine_legal_complete':valid['hinted']==16,'gate_pass':counts['hinted']>=14 and counts['hinted']-counts['unhinted']>=4 and valid['hinted']==16,'all_requests_drained':True,'raw_envelope_reparse_reason':'Original inline equality check treated absent tool_calls key and normalized empty list as unequal. Saved exact envelopes replayed via existing parser; no calls repeated or outputs changed.','agreement_rule':'betting_action(action_args(reply)); amount only bet/raise, others ignored','native_training_GO':False}
(R/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
