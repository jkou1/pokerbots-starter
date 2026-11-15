"""Read-only progress evidence for long local games, by deployment and time."""
import json,re,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
ROOT=Path(__file__).resolve().parent.parent/'data/experiments'
c=Client(project='vals-hackathon')
MODELS=['vals-hackathon/combined-sft-v3','vals-hackathon/selfplay-ad74c826c9ad','vals-hackathon/ac-vals-model']
while datetime.now(timezone.utc).timestamp()<1794762000:
 now=datetime.now(timezone.utc);out={'updated_at':now.isoformat(),'window_seconds':120,'models':{}}
 for model in MODELS:
  try:
   spec=QuerySpec(source='spans',projects=['vals-hackathon'],columns=[ColumnSpec(field=f) for f in ['start_time','end_time','status','error_message','input']],filters=[FieldFilter(field='model',op='eq',value=model),FieldFilter(field='start_time',op='ge',value=(now-timedelta(seconds=120)).isoformat())],limit=100)
   r=c.analytics.query(spec=spec);hands=[]
   for x in r.rows:
    try:
     last=next((m.get('content','') for m in reversed(json.loads(x['input'])) if m.get('role')=='user'),'');match=re.search(r'## Hand (\d+) (?:of (\d+)|is over)',last)
     if match:hands.append({'hand':int(match.group(1)),'total':int(match.group(2)) if match.group(2) else None,'start':x['start_time']})
    except (ValueError,TypeError):pass
   out['models'][model]={'requests':r.total,'latest_end':r.rows[0]['end_time'] if r.rows else None,'errors':sum(bool(x.get('error_message')) or x['status'] in ['error','failed'] for x in r.rows),'recent_hands':hands[:10]}
  except Exception as e:out['models'][model]={'query_error':str(e)[:300]}
 p=ROOT/'gateway-progress-live.tmp';p.write_text(json.dumps(out,indent=2));p.replace(ROOT/'gateway-progress-live.json')
 print(json.dumps({'time':out['updated_at'],'requests':{k:v.get('requests') for k,v in out['models'].items()},'errors':{k:v.get('errors') for k,v in out['models'].items()}}),flush=True)
 time.sleep(60)
