import json,hashlib,re,sys,gzip,os
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments');P=R.parent;os.umask(0o077)
excluded=set();sources=[]
for file in [P/'mixed-teacher-actions-v1/select.jsonl',P/'mixed-teacher-actions-v1/eval.jsonl',P/'pete-postflop-v1/select.jsonl',P/'pete-postflop-v1/eval.jsonl',P/'pete-postflop-v1/preflop-select.jsonl',E/'arena-incumbent-audit/manifest.jsonl',E/'arena-leader-audit/manifest.jsonl']:
 if not file.exists():continue
 for line in file.open():
  d=json.loads(line);ident=d.get('provenance',{}).get('match_id',d.get('id'))
  if ident:excluded.add(ident)
 sources.append({'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
for file in Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/raw').glob('m_*.json'):excluded.add(file.stem)
f=E/'arena-schema-inspection/actual-arena-input-output.json'
if f.exists():
 for row in json.loads(f.read_text()):
  a=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];m=re.match(r'vals-arena/(m_[^/]+)/',a.get('conversation_id',''))
  if m:excluded.add(m[1])
cutoff=datetime.now(timezone.utc).isoformat();rules={'cutoff_utc':cutoff,'source_inference':'infer_b0f5e9429b7e','source_model':'incumbent C / ckpt_51eee61470f7','lower_bound_utc':'2026-11-15T10:52:00Z','max_query_rows':512,'whole_match_split':'sha256(c-cleanup-opsd-v1|matchID),firstbyte<205 train,<231 select,else final','excluded_match_ids':sorted(excluded),'exclusion_sources':sources,'tools_contract':'Published main opsd/tools.json for both sides; original Arena offered definitions absent from telemetry','no_model_calls':True}
(R/'source-rules.json').write_text(json.dumps(rules,indent=2)+'\n');(R/'raw').mkdir(exist_ok=True);(R/'raw').chmod(0o700)
c=working_client();result=c.analytics.query(spec=QuerySpec(source='spans',projects=['vals-hackathon'],job_ids=['infer_b0f5e9429b7e'],columns=[ColumnSpec(field=f)for f in ['start_time','end_time','job_id','trace_id','span_id','name','status','error_message','attributes','input']],filters=[FieldFilter(field='name',op='eq',value='inference.request'),FieldFilter(field='start_time',op='ge',value=rules['lower_bound_utc']),FieldFilter(field='start_time',op='le',value=cutoff)],limit=512,sort_by='start_time',sort_order='desc'))
counts={'queried_rows':len(result.rows),'reported_total':result.total,'actual_arena_rows':0,'cleanup_inputs':0,'excluded_cleanup':0,'long_cleanup_after_exclusions':0,'train_long_contexts':0};contexts=[];groups=set();held=set();seen=set()
with gzip.open(R/'raw/source-rows.jsonl.gz','wt')as out:
 for row in result.rows:
  attrs=json.loads(row['attributes'])if isinstance(row['attributes'],str)else row['attributes'];m=re.fullmatch(r'vals-arena/(m_[^/]+)/hand-(\d+)/seat(\d+)',str(attrs.get('conversation_id','')))
  if not m:continue
  counts['actual_arena_rows']+=1;items=json.loads(row['input']);last=next((x.get('content','')for x in reversed(items)if x.get('role')=='user'),'')
  if 'Now call update_scratchpad'not in last:continue
  counts['cleanup_inputs']+=1
  if m[1]in excluded:counts['excluded_cleanup']+=1;continue
  memory=''
  for item in items:
   if item.get('role')=='user':
    sp=re.search(r'<<<SCRATCHPAD\n(.*?)\nSCRATCHPAD>>>',item.get('content',''),re.S)
    if sp:memory=sp[1];break
  out.write(json.dumps(row)+'\n')
  if len(memory)<1000:continue
  key=(m[1],int(m[2]),int(m[3]),hashlib.sha256(row['input'].encode()).hexdigest())
  if key in seen:continue
  seen.add(key);counts['long_cleanup_after_exclusions']+=1;groups.add(m[1]);bucket=hashlib.sha256(('c-cleanup-opsd-v1|'+m[1]).encode()).digest()[0];split='train'if bucket<205 else'select'if bucket<231 else'eval'
  if split!='train':held.add(m[1]);continue
  counts['train_long_contexts']+=1;contexts.append({'split':split,'source_match_id':m[1],'hand':int(m[2]),'seat':int(m[3]),'incoming_memory_characters':len(memory),'original_input_json_exact':row['input'],'original_input_sha256':key[3],'span_id':row['span_id'],'trace_id':row['trace_id'],'start_time':row['start_time'],'conversation_id':attrs['conversation_id'],'source_inference_id':'infer_b0f5e9429b7e','source_inference_version':attrs.get('inference_version'),'canonical_tools_sha256':hashlib.sha256(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_bytes()).hexdigest(),'status':'genuine_long_input_pending_observability_fact_audit'})
(R/'genuine-train-contexts.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in contexts));counts.update(distinct_long_matches=len(groups),train_distinct_matches=len({x['source_match_id']for x in contexts}),heldout_long_matches=len(held),cutoff_utc=cutoff,source_access='working',full_input_bytes_present=True,no_model_calls=True)
(R/'source-counts.json').write_text(json.dumps(counts,indent=2)+'\n');print(json.dumps(counts,indent=2))
