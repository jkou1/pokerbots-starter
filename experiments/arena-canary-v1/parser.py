"""Read-only protocol checks from actual decision-time observations and outputs."""
import json,re,hashlib
from datetime import datetime,timezone
ARENA=re.compile(r'^vals-arena/(?P<match>m_[^/]+)/hand-(?P<hand>\d+)/seat(?P<seat>\d+)$')
def decoded(value):
 return json.loads(value) if isinstance(value,str) else value
def content_text(value):
 if isinstance(value,str):return value
 if isinstance(value,list):return '\n'.join(x.get('text',x.get('content','')) for x in value if isinstance(x,dict))
 return ''
def parse_legal(text):
 match=re.search(r'^Legal actions:\s*(.+)$',text,re.M)
 if not match:return None
 items=[x.strip() for x in match[1].split(',')];legal={}
 for item in items:
  if item in ['fold','check']:legal[item]=True
  elif m:=re.fullmatch(r'call\s+(\d+)',item):legal['call']=int(m[1])
  elif m:=re.fullmatch(r'(bet|raise) to (\d+)-(\d+)',item):legal[m[1]]=[int(m[2]),int(m[3])]
  else:return None
 return legal
TALK_PATTERNS=[r'\bfuck(?:ing|ed|er)?\b',r'\bshit(?:ty)?\b',r'\basshole\b',r'\b(?:idiot|moron|retard(?:ed)?)\b',r'\b(?:rape|porn|blowjob)\b',r'\bkill yourself\b']
def analyze(row,require_arena=True):
 attrs=decoded(row.get('attributes') or {})
 conversation=str(attrs.get('conversation_id',''));match=ARENA.fullmatch(conversation)
 if require_arena and not match:return None
 result={'span_id':row.get('span_id',row.get('trace_id')),'trace_id':row.get('trace_id'),'start_time':row.get('start_time'),'conversation_id':conversation,'match_id':match['match'] if match else None,'hand':int(match['hand']) if match else None,'seat':int(match['seat']) if match else None,'version':attrs.get('inference_version'),'inference_id':attrs.get('inference_deployment_id',row.get('job_id')),'errors':[],'critical':[],'unsupported':['Arena tool definitions and optional p_win/read requirements unavailable','Cleanup factual correctness is not inferred from protocol validity','Talk screening is a bounded lexical flagger, not complete moderation']}
 errors=result['errors'];critical=result['critical']
 try:
  inputs=decoded(row.get('input') or []);users=[x for x in inputs if x.get('type')=='message' and x.get('role')=='user'];text=content_text(users[-1]['content']) if users else ''
 except (ValueError,TypeError,KeyError):text='';errors.append('malformed_observed_input')
 cleanup='Now call update_scratchpad' in text;result['kind']='cleanup' if cleanup else 'decision'
 result['observation_sha256']=hashlib.sha256(text.encode()).hexdigest()
 result['logical_turn_id']=hashlib.sha256((conversation+'|'+result['kind']+('' if cleanup else '|'+result['observation_sha256'])).encode()).hexdigest()
 street=re.search(r'^Street:\s*(\w+)',text,re.M);result['street']=street[1] if street else None
 legal=parse_legal(text) if not cleanup else None;result['legal_text_supported']=legal is not None
 if not cleanup and legal is None:result['unsupported'].append('Visible legal-actions text missing or unsupported; sizing legality unverified')
 reason=str(attrs.get('finish_reason','')).lower();result['truncated']=reason in ['length','max_tokens','max_output_tokens','token_limit']
 if result['truncated']:errors.append('token_truncation')
 http=attrs.get('http_status_code')
 if isinstance(http,(int,float)) and http>=400:critical.append('endpoint_http_error')
 if row.get('error_message') or str(row.get('status','')).lower() in ['error','failed']:critical.append('span_error')
 try:
  outputs=decoded(row.get('output') or []);assert isinstance(outputs,list)
  calls=[x for x in outputs if x.get('type')=='function_call']
 except (ValueError,TypeError,AssertionError):calls=[];errors.append('malformed_runtime_output')
 result['tool_calls']=len(calls)
 if len(calls)!=1:errors.append('missing_tool_call' if not calls else 'multiple_tool_calls')
 if calls:
  call=calls[0];expected='update_scratchpad' if cleanup else 'submit_action'
  if call.get('name')!=expected:errors.append('wrong_tool')
  try:
   args=decoded(call.get('arguments'));assert isinstance(args,dict)
  except (ValueError,TypeError,AssertionError):args={};errors.append('malformed_tool_arguments')
  if cleanup:
   contents=args.get('contents');result['contents_characters']=len(contents) if isinstance(contents,str) else None
   if not isinstance(contents,str):errors.append('cleanup_contents_not_string')
   elif len(contents)>5000:errors.append('cleanup_contents_too_long')
   if set(args)-{'contents'}:errors.append('cleanup_unknown_argument_keys')
  else:
   action=args.get('action');result['action']=action if isinstance(action,str) else None
   if action not in ['fold','check','call','bet','raise']:errors.append('invalid_action_enum')
   elif legal is not None:
    if action not in legal:errors.append('action_not_legal')
    elif action in ['bet','raise']:
     amount=args.get('amount')
     if type(amount) is not int:errors.append('amount_not_integer')
     elif not legal[action][0]<=amount<=legal[action][1]:errors.append('amount_outside_visible_street_total_bounds')
   elif action in ['bet','raise'] and (type(args.get('amount')) is not int or args['amount']<=0):errors.append('invalid_core_amount')
   say=args.get('say');result['say_present']=bool(say)
   if isinstance(say,str) and any(re.search(p,say,re.I) for p in TALK_PATTERNS):critical.append('workplace_talk_flag')
 if 'malformed_runtime_output' in errors or 'malformed_tool_arguments' in errors:critical.append('unparseable_output')
 if 'missing_tool_call' in errors:critical.append('no_tool_call')
 if result['truncated']:critical.append('token_truncation')
 result['errors']=sorted(set(errors));result['critical']=sorted(set(critical));result['valid_protocol']=not errors and not critical;return result
