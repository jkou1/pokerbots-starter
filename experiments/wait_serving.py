"""Bounded ready+real-tool check, using the user-required new account's existing key."""
import argparse,json,os,time
from pathlib import Path
import httpx
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
from vals_tools.deploy import PROBE_TOOL,PROBE_MESSAGES,INFERENCE_URL
p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--model',required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c);start=time.monotonic()
while time.monotonic()-start<720:
 i=c.inference.get(a.id);print(a.id,i.state,flush=True)
 if i.state in ['ready','running','healthy']:
  try:
   r=httpx.post(INFERENCE_URL+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['AC2_API_KEY']},json={'model':a.model,'messages':PROBE_MESSAGES,'tools':[PROBE_TOOL],'max_completion_tokens':5000,'chat_template_kwargs':{'enable_thinking':True}},timeout=60)
   calls=r.json()['choices'][0]['message'].get('tool_calls') if r.is_success else None
   if calls and calls[0]['function']['name']=='submit_action' and json.loads(calls[0]['function']['arguments']).get('action') in ['fold','check','call','bet','raise']:
    old=json.loads(a.receipt.read_text()) if a.receipt.exists() else {};old.update(ready_verified_at=time.time(),probe_http_status=r.status_code,probe_tool_calls=calls,probe_identity=identity);a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(old,indent=2));print('READY_REAL_TOOL_PROBE_PASS',a.id,flush=True);break
   print('probe_http',r.status_code,'calls',bool(calls),flush=True)
  except Exception as e:print('probe_error',type(e).__name__,flush=True)
 time.sleep(10)
else:raise RuntimeError('Serving deadline12min exceeded; inspect existing request, do not duplicate')
