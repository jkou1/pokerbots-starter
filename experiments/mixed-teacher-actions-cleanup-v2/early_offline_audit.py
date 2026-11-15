"""Bounded read-only audit of any available offline token rows before optimizer metrics."""
import collections,json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main');from vals_tools.sft_audit import audit_target
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec
R=Path(__file__).resolve().parent;c=working_client();pmap=json.loads((R/'task-provenance-map.json').read_text());run='train_41ab837f39e5'
r=c.analytics.query(spec=QuerySpec(source='token_viz',job_ids=[run],columns=[ColumnSpec(field=x) for x in ['step','payload','loss']],sort_by='step',sort_order='asc',limit=256));steps={}
for row in r.rows:
 p=json.loads(row['payload']);step=str(row['step']);s=steps.setdefault(step,{'observed_rows':0,'kinds':collections.Counter(),'errors':[],'unique_sequences':set()});s['observed_rows']+=1;s['unique_sequences'].add((p['sample_index'],p.get('segment_index')));source=pmap.get(p['datapoint_id'])
 if source is None:s['errors'].append('unknown_task_id');continue
 s['kinds'][source.get('teacher','genuine-own-cleanup')]+=1
 if any(t in p['student_prompt'] for t in ['house-professor-pete','house-chatty-carlos']):s['errors'].append('teacher_identity_in_student_prompt')
 try:
  audit_target(p);text=''.join(p['sampled_tokens']);assert text.count('</think>')==1 and text.count('<tool_call>')==text.count('</tool_call>')==1
  expected='update_scratchpad' if source.get('control_kind') else 'submit_action';assert f'<function={expected}>' in text
 except Exception as e:s['errors'].append(type(e).__name__+':'+str(e))
for s in steps.values():s['kinds']=dict(s['kinds']);s['unique_sequences']=len(s['unique_sequences'])
report={'at':datetime.now(timezone.utc).isoformat(),'train_id':run,'stage':'offline token trace availability, independent of optimizer metric publication','steps':steps,'status':'available' if steps else 'not_available_yet','no_model_calls':True,'no_job_or_dataset_mutation':True}
(R/'early-offline-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
