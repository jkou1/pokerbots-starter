"""Versioned TRAIN/SELECT upload only. Never reads/uploads FINAL or launches jobs."""
import json,hashlib,os,sys,time
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
from ac2.runtime import Task,compute_content_hash
R=Path(__file__).resolve().parent;receiptfile=R/'upload-receipt.json';lock=R/'upload.pid';os.umask(0o077)
if lock.exists():
 try:os.kill(int(lock.read_text()),0)
 except (ProcessLookupError,ValueError):lock.unlink()
 else:raise SystemExit('Existing upload handle alive; do not duplicate')
lock.write_text(str(os.getpid()))
def members(c,name):
 result={};offset=0
 while True:
  page=c.datasets.list_tasks(name,offset=offset,limit=1000);result.update({x.content_hash:x.id for x in page})
  if len(page)<1000:return result
  offset+=len(page)
try:
 assert json.loads((R/'boundary-audit.json').read_text())['weighted_train_audited']==7369
 c=working_client();identity=preflight_identity(c);receipt=json.loads(receiptfile.read_text())if receiptfile.exists()else{'identity':identity,'final_untouched':True}
 for split,file,name in [('train','weighted-train-tasks.jsonl','pokerbots-pokerbench-v5-reconciled-pre10x-train'),('select','select-tasks.jsonl','pokerbots-pokerbench-v5-reconciled-select')]:
  tasks=[Task.model_validate_json(l)for l in(R/file).open()];expected={compute_content_hash(t):t for t in tasks};assert len(expected)==len(tasks);preflight_identity(c);dataset=c.datasets.create(name,description='3499postflop incl2439pot+1reconciled providerlabels ofuncertaincorrected-stateoptimality;387pre10x. Version5,no FINAL.',exist_ok=True);actual=members(c,name);assert set(actual)<=set(expected),'Unexpected content in versioned dataset; refuse mutation';receipt[split]={'name':name,'dataset_id':dataset.id,'expected':len(expected),'file_sha256':hashlib.sha256((R/file).read_bytes()).hexdigest(),'status':'uploading'};receiptfile.write_text(json.dumps(receipt,indent=2)+'\n');missing=[t for h,t in expected.items()if h not in actual]
  for start in range(0,len(missing),500):
   preflight_identity(c);c.datasets.add_tasks(name,tasks=missing[start:start+500]);receipt[split]['submitted_missing']=min(start+500,len(missing));receiptfile.write_text(json.dumps(receipt,indent=2)+'\n');print(split,'submitted',min(start+500,len(missing)),'/',len(missing),flush=True)
  actual=members(c,name);assert set(actual)==set(expected);sample=[]
  for h in sorted(expected)[::max(1,len(expected)//5)][:5]:
   loaded=c.datasets.load_task(actual[h]);assert loaded.content_hash==h;assert loaded.input==expected[h].input;assert loaded.env_params==expected[h].env_params;sample.append({'task_id':actual[h],'content_hash':h,'exact_input_env_payload_verified':True})
  receipt[split].update(status='verified',remote_count=len(actual),full_membership_equal=True,sampled_payloads=sample);receiptfile.write_text(json.dumps(receipt,indent=2)+'\n');print(split,'VERIFIED',len(actual),flush=True)
finally:
 lock.unlink(missing_ok=True)
