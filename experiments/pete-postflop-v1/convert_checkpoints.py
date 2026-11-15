"""Prepare registered iteration19 checkpoints for serving, without deployments."""
import dataclasses,json,time
from datetime import datetime,timezone
from pathlib import Path
from ac2.sdk import Client
ROOT=Path(__file__).resolve().parent
c=Client(project='vals-hackathon')
ids=[json.loads((ROOT/name).read_text())['train_id'] for name in ['run.json','base-control-run.json']]
p=ROOT/'conversion-status.json';receipts=json.loads(p.read_text()) if p.exists() else {}
while True:
 finished=0
 for train in ids:
  try:
   checkpoints=c.checkpoints.list(train_job_id=train)
   found=[x for x in checkpoints if x.iter_num==19]
   if not found:
    print(datetime.now(timezone.utc).isoformat(),train,'waiting for iteration19',flush=True)
    continue
   ckpt=found[0];state=str(c.checkpoints.promotion_status(ckpt.id).state)
   prior=receipts.get(ckpt.id,{})
   if state in ['missing','none','not_found'] and not prior.get('requested'):
    receipts[ckpt.id]={'train_id':train,'iter_num':19,'requested':True,'requested_at':datetime.now(timezone.utc).isoformat(),'state_before':state}
    p.write_text(json.dumps(receipts,indent=2)+'\n')
    state=str(c.checkpoints.promote(ckpt.id).state)
   receipts.setdefault(ckpt.id,{'train_id':train,'iter_num':19})
   receipts[ckpt.id].update(state=state,updated_at=datetime.now(timezone.utc).isoformat())
   p.write_text(json.dumps(receipts,indent=2)+'\n')
   print(datetime.now(timezone.utc).isoformat(),train,ckpt.id,state,flush=True)
   if state in ['available','ready','succeeded','completed','converted']:finished+=1
  except Exception as e:print(datetime.now(timezone.utc).isoformat(),train,type(e).__name__,str(e),flush=True)
 if finished==len(ids):break
 time.sleep(30)
