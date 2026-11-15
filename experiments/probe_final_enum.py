"""One selected candidate's exact final-error regression replay; never training/model ranking."""
import asyncio,json,os,re
from pathlib import Path
import httpx
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL
from poker_harness.prompts import parse_tool_call
root=Path(__file__).resolve().parent.parent/'data/experiments/sealed-final-base20-v1';cases=json.loads((root/'candidate/exact-enum-failures.json').read_text())['cases'];results=[]
def messages(items):
 out=[]
 for item in items:
  if item['type']=='message':out.append({'role':item['role'],'content':item.get('content','')})
  elif item['type']=='function_call':
   if not out or out[-1]['role']!='assistant':out.append({'role':'assistant','content':''})
   out[-1].setdefault('tool_calls',[]).append({'id':item['call_id'],'type':'function','function':{'name':item['name'],'arguments':item['arguments']}})
  elif item['type']=='function_call_output':out.append({'role':'tool','tool_call_id':item['call_id'],'content':item['output']})
  elif item['type']!='reasoning':raise ValueError('Unsupported source runtime item')
 return out
async def run():
 sem=asyncio.Semaphore(2)
 async with httpx.AsyncClient(timeout=90)as client:
  complete=relay_completion(client,GATEWAY_URL,os.environ['AC2_API_KEY'],with_preset({'preset':'event','model_label':'infer_9efa1c614a32','submit_fields':['action','amount','say']}))
  async def one(case,index):
   async with sem:
    reply=await asyncio.wait_for(complete(messages(json.loads(case['span']['input']))),timeout=90);calls=[x for x in reply.tool_calls if x['function']['name']=='submit_action'];decision,error=parse_tool_call(calls[0]['function']['arguments'],talk=True)if len(calls)==1 else(None,'expected one submit_action');bound=re.search(r'raise to (\d+)-(\d+)',case['last_user']);valid=decision is not None and not error and not reply.truncated and len(reply.tool_calls)==1 and (decision.type in ['fold','call']or decision.type=='raise'and type(decision.amount)is int and bound is not None and int(bound[1])<=decision.amount<=int(bound[2]));r={'seed':case['seed'],'hand':case['hand'],'sample':index,'legal':bool(valid),'error':error,'tool_calls':reply.tool_calls,'truncated':reply.truncated};results.append(r);print(json.dumps(r),flush=True)
  await asyncio.gather(*(one(case,index)for case in cases for index in range(4)))
 out={'scope':'Exact final failure-state regression on frozen selected20 only; not training or further checkpoint selection. Same effective action/amount/say tools.','checkpoint':'ckpt_11e7c430069c','samples':len(results),'legal':sum(r['legal']for r in results),'results':results};(root/'candidate/enum-regression-repeats.json').write_text(json.dumps(out,indent=2)+'\n')
asyncio.run(run())
