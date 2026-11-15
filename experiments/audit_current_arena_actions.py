"""Bounded read-only OWN actual Arena protocol audit; no model calls/strategy labels."""
import hashlib,json,os,re,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
from poker_harness.prompts import sanitize_talk
R=Path('data/experiments/current-arena-action-audit');R.mkdir(exist_ok=True);now=datetime.now(timezone.utc);cutoff=now-timedelta(minutes=60);c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);q=QuerySpec(source='spans',projects=['vals-hackathon'],job_ids=['infer_b0f5e9429b7e'],columns=[ColumnSpec(field=x)for x in['start_time','end_time','span_id','status','error_message','attributes','input','output']],filters=[FieldFilter(field='name',op='eq',value='inference.request'),FieldFilter(field='start_time',op='ge',value=cutoff.isoformat())],limit=250,sort_by='start_time',sort_order='desc');response=c.analytics.query(spec=q);raw=json.dumps(response.rows,ensure_ascii=False).encode();stamp=now.strftime('%Y%m%dT%H%M%SZ');rawpath=R/(stamp+'-raw.json');rawpath.write_bytes(raw);selected=[];skips={};
def skip(reason):skips[reason]=skips.get(reason,0)+1
for row in response.rows:
 if len(selected)>=100:break
 try:
  attrs=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];ids=[v for v in attrs.values()if isinstance(v,str)and v.startswith('vals-arena/')]
  if not ids:skip('not_positive_arena');continue
  if not row.get('end_time'):skip('inflight');continue
  inputs=json.loads(row['input'])if isinstance(row['input'],str)else row['input'];output=json.loads(row['output'])if isinstance(row['output'],str)else row['output'];latest=next((x.get('content','')for x in reversed(inputs)if x.get('role')=='user'),'')
  if 'Now call update_scratchpad'in latest or 'update_scratchpad exactly once'in latest:skip('cleanup');continue
  if 'Legal actions:'not in latest:skip('not_identifiable_action');continue
  legal=latest.rsplit('Legal actions:',1)[1].splitlines()[0];calls=[x for x in output if x.get('type')=='function_call'];reasons=[];args={};say='';call=calls[0]if len(calls)==1 else{}
  if len(calls)!=1:reasons.append('missing_or_multiple_real_calls')
  elif call.get('name')!='submit_action':reasons.append('wrong_tool')
  else:
   try:args=json.loads(call.get('arguments',''));action=args.get('action');say=args.get('say')or''
   except (ValueError,AttributeError):reasons.append('unreadable_arguments');action=None
   if action not in['fold','check','call','bet','raise']:reasons.append('invalid_enum')
   elif action in['bet','raise']:
    bounds=re.search(r'\b(?:bet|raise) to (\d+)-(\d+)',legal);amount=args.get('amount')
    if bounds is None or type(amount)is not int or not int(bounds[1])<=amount<=int(bounds[2]):reasons.append('illegal_amount_or_action')
   elif action=='check'and not re.search(r'\bcheck\b',legal):reasons.append('illegal_action')
  sampling=attrs.get('sampling_params',{});sampling=json.loads(sampling)if isinstance(sampling,str)else sampling;truncated=attrs.get('finish_reason')in['length','max_tokens']
  if truncated:reasons.append('truncated')
  if row.get('error_message')or str(row.get('status')).lower()in['error','failed']:reasons.append('request_error')
  selected.append({'span_id':row['span_id'],'start':row['start_time'],'end':row['end_time'],'arena_conversation_id':ids[0],'real_tool_names':[x.get('name')for x in calls],'invalid_reasons':reasons,'finish_reason':attrs.get('finish_reason'),'sampling_params':sampling,'nonempty_raw_say':bool(say),'raw_say_type':type(say).__name__,'raw_say_characters':len(say)if isinstance(say,str)else None,'sanitized_say':sanitize_talk(say)if isinstance(say,str)else'','legal_prompt_verified':True})
 except Exception as exc:skip('parse_error_'+type(exc).__name__)
counts={}
for x in selected:
 for reason in x['invalid_reasons']:counts[reason]=counts.get(reason,0)+1
report={'scope':'OWNcurrentC actualArena request completions, monitoringonly; not publicdashboard coverage, strategy evaluation or final selection. Validity inferred from realtools+visiblelegalprompt+finish metadata; Arena fallback acceptance not observed.','inference_id':'infer_b0f5e9429b7e','checkpoint':'ckpt_51eee61470f7','cutoff_utc':cutoff.isoformat(),'queried_at':now.isoformat(),'query_limit':250,'source_rows_returned':len(response.rows),'action_limit':100,'actual_arena_action_completions':len(selected),'skipped':skips,'invalid_or_truncated':sum(bool(x['invalid_reasons'])for x in selected),'invalid_reason_counts':counts,'real_submit_action_single':sum(x['real_tool_names']==['submit_action']for x in selected),'truncated':sum('truncated'in x['invalid_reasons']for x in selected),'action_cap5000_exposed':sum(x['sampling_params'].get('max_completion_tokens',x['sampling_params'].get('max_tokens'))==5000 for x in selected),'raw_say_nonempty':sum(x['nonempty_raw_say']for x in selected),'sanitized_say_nonempty':sum(bool(x['sanitized_say'])for x in selected),'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_path':str(rawpath.resolve()),'first_observed':selected[-1]['start']if selected else None,'last_observed':selected[0]['start']if selected else None,'no_model_calls':True,'no_deployment_changes':True};(R/(stamp+'-selected-private.json')).write_text(json.dumps(selected,indent=2)+'\n');(R/'latest-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
