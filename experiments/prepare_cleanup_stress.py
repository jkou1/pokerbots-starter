import json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from ac2.sdk import Client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
ROOT=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/cleanup-stress-select-v1');ROOT.mkdir(parents=True,exist_ok=True)
c=Client(project='vals-hackathon');records=[];summaries={};raw=[]
for model in ['vals-hackathon/combined-sft-v3','vals-hackathon/selfplay-ad74c826c9ad']:
 q=QuerySpec(source='spans',projects=['vals-hackathon'],columns=[ColumnSpec(field=f) for f in ['span_id','trace_id','start_time','end_time','model','input','output','attributes']],filters=[FieldFilter(field='model',op='eq',value=model),FieldFilter(field='start_time',op='ge',value='2026-11-15T08:38:00')],limit=500)
 response=c.analytics.query(spec=q);count=0;over=0;kept=0;seen=set()
 for x in response.rows:
  try:
   messages=json.loads(x['input']);reply=json.loads(x['output']);reply=json.loads(reply) if isinstance(reply,str) else reply
   if not isinstance(messages,list) or not messages or 'game lasts 30 hands' not in messages[0].get('content',''):continue
   last=next((m.get('content','') for m in reversed(messages) if m.get('role')=='user'),'')
   if '## Hand ' not in last or 'is over' not in last:continue
   calls=[i for i in reply if i.get('type')=='function_call' and i.get('name')=='update_scratchpad']
   if len(calls)!=1:continue
   contents=json.loads(calls[0]['arguments'])['contents'];count+=1;over+=len(contents)>5000
   digest=hashlib.sha256(x['input'].encode()).hexdigest()
   if len(contents)<=5000 or kept>=5 or digest in seen:continue
   seen.add(digest);kept+=1;raw.append(x)
   records.append({'split':'select','model':model,'source':'own local official30hand selection collection; exact deployment label excludes Arena inferenceID','provenance':{'span_id':x['span_id'],'trace_id':x['trace_id'],'start_time':x['start_time'],'input_sha256':digest},'messages':messages,'observed_reply':reply,'observed_contents_characters':len(contents),'test':'must emit one update_scratchpad with factual contents <=5000chars; prefer <=1500chars; do not train this selection case'})
  except (ValueError,TypeError,KeyError):continue
 summaries[model]={'queried_rows':len(response.rows),'available_rows':response.total,'cleanup_initial_calls_in_sample':count,'over_5000':over,'stress_kept':kept,'coverage':'bounded latest500 gateway rows, not complete-game rate'}
(ROOT/'select.jsonl').write_text('\n'.join(json.dumps(x) for x in records)+'\n');(ROOT/'source_rows.json').write_text(json.dumps(raw,indent=2));manifest={'cutoff':datetime.now(timezone.utc).isoformat(),'source':'AC2 project gateway spans','summary':summaries,'selection_cases':len(records),'sha256':hashlib.sha256((ROOT/'select.jsonl').read_bytes()).hexdigest()};(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
