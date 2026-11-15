"""Resumable content-verified upload; never launches training."""
import hashlib,json,time
from pathlib import Path
import httpx
from ac2.runtime import Task,compute_content_hash
import sys
sys.path.insert(0,'/tmp')
from pokerbots_working_client import working_client,preflight_identity
ROOT=Path(__file__).resolve().parent

def members(c,name):
 actual={};offset=0
 while True:
  page=c.datasets.list_tasks(name,offset=offset,limit=1000)
  actual.update({r.content_hash:r.id for r in page})
  if len(page)<1000:return actual
  offset+=len(page)

def main():
 c=working_client();identity=preflight_identity(c);receipt={}
 receipt_file=ROOT/'upload.json'
 if receipt_file.exists():receipt=json.loads(receipt_file.read_text())
 for split in ['train']:
  name=f'pokerbots-mixed-pete-carlos-actions-cleanup-v2-{split}'
  tasks=[Task.model_validate_json(l) for l in (ROOT/f'{split}-tasks.jsonl').open()]
  expected={compute_content_hash(t):t for t in tasks}
  preflight_identity(c)
  d=c.datasets.create(name,description='7640unchangedPeteCarlosactions+80samplingcopiesof4genuineowncleanupTRAIN;protocolretentionv2.',exist_ok=True)
  actual=members(c,name)
  if not set(actual)<=set(expected):raise ValueError('Unexpected remote data; refuse mutation')
  missing=[t for h,t in expected.items() if h not in actual]
  receipt[split]={'name':name,'dataset_id':d.id,'expected':len(expected),'source_sha256':hashlib.sha256((ROOT/f'{split}-tasks.jsonl').read_bytes()).hexdigest(),'status':'uploading','identity':identity}
  for start in range(0,len(missing),500):
   for retry in range(5):
    try:
     preflight_identity(c)
     ids=c.datasets.add_tasks(name,tasks=missing[start:start+500]);break
    except (httpx.HTTPStatusError,httpx.RequestError) as e:
     if isinstance(e,httpx.HTTPStatusError) and e.response.status_code not in [408,429,500,502,503,504,520,522,524]:raise
     if retry==4:raise
     time.sleep(min(2**retry,8))
   receipt[split]['last_chunk_ids']=ids;receipt_file.write_text(json.dumps(receipt,indent=2)+'\n')
   print(name,start+len(ids),'/',len(missing),flush=True)
  actual=members(c,name)
  if set(actual)!=set(expected):raise ValueError('Remote membership mismatch')
  sample=[]
  for h in [*expected][::max(1,len(expected)//3)][:3]:
   loaded=c.datasets.load_task(actual[h])
   if loaded.content_hash!=h:raise ValueError('Retrieved sample hash mismatch')
   sample.append(actual[h])
  receipt[split].update(status='verified',count=len(actual),task_ids=actual,sampled_ids=sample)
  receipt_file.write_text(json.dumps(receipt,indent=2)+'\n')
  print(name,'VERIFIED',len(actual),flush=True)
if __name__=='__main__':main()
