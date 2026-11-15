import json,sys,os
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
os.umask(0o077);R=Path(__file__).resolve().parent;p=json.loads((R/'paired-first10-policy.json').read_text());since=datetime.fromtimestamp(p['locked_at'],timezone.utc).isoformat();c=working_client()
r=c.analytics.query(spec=QuerySpec(source='spans',projects=['vals-hackathon'],job_ids=[p['model']],columns=[ColumnSpec(field=f)for f in ['start_time','end_time','job_id','trace_id','span_id','name','status','error_message','attributes','input','output']],filters=[FieldFilter(field='name',op='eq',value='inference.request'),FieldFilter(field='start_time',op='ge',value=since)],limit=64,sort_by='start_time',sort_order='desc'))
(R/'raw/paired-gateway-spans.json').write_text(json.dumps(r.rows,indent=2)+'\n');print(json.dumps({'rows':len(r.rows),'total':r.total,'since':since}))
