"""Persistent job monitor; writes status, checkpoints, sampled target audit every30s."""
import dataclasses,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.analytics.types import ColumnSpec,QuerySpec
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from audit import audit_target
c=Client(project='vals-hackathon');train=json.loads((ROOT/'base-control-run.json').read_text())['train_id']
while True:
 try:
  info=c.train.get(train);checkpoints=c.checkpoints.list(train_job_id=train)
  status={'updated_at':datetime.now(timezone.utc).isoformat(),'train':dataclasses.asdict(info),'checkpoints':[dataclasses.asdict(x) for x in checkpoints]}
  result=c.analytics.query(spec=QuerySpec(source='token_viz',job_ids=[train],columns=[ColumnSpec(field=x) for x in ['step','payload','response_length','loss']],sort_by='step',limit=8))
  if result.rows:
   samples=[{'step':r['step'],'payload':json.loads(r['payload'])} for r in result.rows]
   (ROOT/'base-control-token-samples.json').write_text(json.dumps(samples,indent=2)+'\n')
   try:status['token_audit']={'passed':True,'samples':[audit_target(r['payload']) for r in samples]}
   except Exception as e:status['token_audit']={'passed':False,'error':str(e)}
  (ROOT/'base-control-status.json').write_text(json.dumps(status,indent=2,default=str)+'\n')
  print(status['updated_at'],info.status,len(checkpoints),'checkpoints',status.get('token_audit',{}).get('passed'),flush=True)
  if info.completed:break
 except Exception as e:
  print(datetime.now(timezone.utc).isoformat(),type(e).__name__,str(e),flush=True)
 time.sleep(30)
