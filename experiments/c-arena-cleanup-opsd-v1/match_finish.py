import json,collections
from pathlib import Path
R=Path(__file__).resolve().parent;rows=json.loads((R/'raw/paired-gateway-spans.json').read_text());results=json.loads((R/'raw/paired-first10-results.json').read_text());audit=[]
for i,case in enumerate(results['results']):
 for arm,v in case['arms'].items():
  ids={x['call_id']for x in v['runtime_items_exact']if x['type']=='function_call'};matched=[]
  for row in rows:
   out=json.loads(row['output'])if isinstance(row['output'],str)else row['output'];rid={x.get('call_id')for x in out if x['type']=='function_call'}
   if ids and ids==rid:matched.append((row,out))
  assert len(matched)==1;row,out=matched[0];a=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];original=json.loads(row['input'])if isinstance(row['input'],str)else row['input'];assert original==v['input_runtime_items'];assert out==[{k:z for k,z in x.items()if z is not None}for x in v['runtime_items_exact']];audit.append({'case':i+1,'arm':arm,'span_id':row['span_id'],'trace_id':row['trace_id'],'finish_reason':a.get('finish_reason'),'end_time':row['end_time'],'status':row['status'],'exact_input_match':True,'exact_runtime_reply_match_after_removing_sdk_null_defaults':True,'version':a.get('inference_version')})
report={'cases':10,'matched_arms':len(audit),'finish_counts':dict(collections.Counter(x['finish_reason']for x in audit)),'all_exact_input_and_output_matches':True,'http_wire_envelope_available':False,'gateway_runtime_items_and_finish_recovered':True,'arms':audit};(R/'paired-first10-finish-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='arms'},indent=2))
