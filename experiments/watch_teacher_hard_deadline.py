"""Probe a recreated teacher; independent timer retires once at creation+8min if unready."""
import argparse,json,os,threading,time
from pathlib import Path
import httpx
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
from vals_tools.deploy import INFERENCE_URL,PROBE_MESSAGES,PROBE_TOOL
p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();r=json.loads(a.receipt.read_text());mid=r['inference_id'];deadline=r['requested_at']+480;key=os.environ['AC2_API_KEY'];c=Client(project='vals-hackathon',api_key=key);guard_client=Client(project='vals-hackathon',api_key=key);identity=preflight_identity(c);guard_identity=preflight_identity(guard_client);lock=threading.Lock();state={'ready':bool(r.get('ready_verified')),'expired':False};r['hard_ready_deadline_at']=deadline;r['guard_identity_preflight']=guard_identity

def save():
 temp=a.receipt.with_suffix('.tmp');temp.write_text(json.dumps(r,indent=2)+'\n');temp.replace(a.receipt)

def retire():
 with lock:
  if state['ready']:return
  state['expired']=True;r['deadline_retirement_requested_at']=time.time();r['deadline_retirement_reason']='No real-tool ready before actual creation+480seconds; collector never activated';save()
 print('HARD_DEADLINE_RETIRE_ONCE',mid,flush=True)
 try:
  guard_client.inference.delete(mid)
  with lock:r['deadline_delete_accepted_at']=time.time();save()
  print('HARD_DEADLINE_DELETE_ACCEPTED',mid,flush=True)
 except Exception as exc:
  with lock:r['deadline_delete_error']=type(exc).__name__+': '+str(exc)[:300];save()
  print('HARD_DEADLINE_DELETE_ERROR',type(exc).__name__,flush=True)

save();timer=threading.Timer(max(0,deadline-time.time()),retire);timer.daemon=False;timer.start()
try:
 while not state['expired'] and time.time()<deadline:
  try:
   model=c.inference.get(mid);print(mid,model.state,'age',round(time.time()-r['requested_at'],1),flush=True)
   if model.deployment:
    with lock:r['dispatch_id']=model.deployment.id;r['last_state']=model.state;r['last_state_at']=time.time();save()
   if model.state in ['ready','running','healthy']:
    remaining=deadline-time.time()
    if remaining<=0:break
    response=httpx.post(INFERENCE_URL+'/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':mid,'messages':PROBE_MESSAGES,'tools':[PROBE_TOOL],'max_completion_tokens':5000,'chat_template_kwargs':{'enable_thinking':True}},timeout=min(20,remaining));calls=response.json()['choices'][0]['message'].get('tool_calls')if response.is_success else None
    good=bool(calls and calls[0]['function']['name']=='submit_action'and json.loads(calls[0]['function']['arguments']).get('action')in ['fold','check','call','bet','raise'])
    if good:
     with lock:
      if state['expired'] or time.time()>=deadline:break
      state['ready']=True;r.update(ready_verified=True,ready_verified_at=time.time(),probe_http_status=response.status_code,probe_tool_calls=calls,probe_identity=identity);save();timer.cancel()
     print('READY_REAL_TOOL_PROBE_PASS',mid,flush=True);break
  except Exception as exc:print('probe_or_state_error',type(exc).__name__,flush=True)
  time.sleep(min(3,max(0,deadline-time.time())))
 if not state['ready']:
  timer.join();raise RuntimeError('Teacherunready;harddeadlineguardretiredrequestonce')
finally:
 if state['ready']:timer.cancel()
