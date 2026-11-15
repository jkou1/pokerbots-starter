"""Selection-only public-state replay; no opponent cards or outcome-derived targets."""
import asyncio,json,os,re,time
from pathlib import Path
from collections import Counter
import httpx
from ac2.sdk import Client
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL
from poker_harness.prompts import parse_tool_call
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/rl-checkpoint-selection/fixed-overbet';ROOT.mkdir(parents=True,exist_ok=True);c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);rows=c.analytics.spans(run_ids=['eval_1712153a22c5']).select('input','start_time','trace_id').filter(name='get_completion',datapoint_id='tsk_b2338320ba30').to_records();selected=None
for row in rows:
 items=json.loads(row['input']);last=next((i.get('content','') for i in reversed(items) if i.get('role')=='user'),'')
 if 'Street: river' in last and re.search(r'call\s+198',last):selected=row;break
if selected is None:raise RuntimeError('Exact river input not found; no reconstructed substitute used')
items=json.loads(selected['input']);messages=[];reasoning_skipped=0
for item in items:
 typ=item['type']
 if typ=='message':messages.append({'role':item['role'],'content':item.get('content','')})
 elif typ=='function_call':
  if not messages or messages[-1]['role']!='assistant':messages.append({'role':'assistant','content':''})
  messages[-1].setdefault('tool_calls',[]).append({'id':item['call_id'],'type':'function','function':{'name':item['name'],'arguments':item['arguments']}})
 elif typ=='function_call_output':messages.append({'role':'tool','tool_call_id':item['call_id'],'content':item['output']})
 elif typ=='reasoning':reasoning_skipped+=1
 else:raise RuntimeError('Unsupported source item '+str(typ))
(ROOT/'input.json').write_text(json.dumps({'source_eval':'eval_1712153a22c5','source_task':'tsk_b2338320ba30','source_trace':selected['trace_id'],'source_time':selected['start_time'],'source_runtime_items':items,'messages':messages,'un_echoed_reasoning_items_skipped':reasoning_skipped,'split':'selection-regression-only','never_train':True},indent=2))
MODELS={'parent-ad74':'vals-hackathon/selfplay-ad74c826c9ad','rl20':'vals-hackathon/grpo-history-ad74-step20','base-sft20':'vals-hackathon/pete-postflop-base-s20-jkou'}
async def run():
 sem=asyncio.Semaphore(2);results=[]
 async with httpx.AsyncClient(timeout=120) as client:
  calls={name:relay_completion(client,GATEWAY_URL,os.environ['AC2_API_KEY'],with_preset({'preset':'event','model_label':model,'submit_fields':['action','amount','say']})) for name,model in MODELS.items()}
  async def one(name,index):
   async with sem:
    try:
     reply=await asyncio.wait_for(calls[name](messages),timeout=120);submits=[x for x in reply.tool_calls if x['function']['name']=='submit_action'];decision,error=parse_tool_call(submits[0]['function']['arguments'],talk=True) if len(submits)==1 else (None,'expected one real submit_action');valid=not error and not reply.truncated and decision.type in ['fold','call'];r={'model':name,'sample':index,'action':decision.type if decision is not None else None,'legal':bool(valid),'parser_error':error,'submitted_tool_calls':reply.tool_calls,'applied_call_cost_if_call':198 if valid and decision.type=='call' else None,'tokens':reply.out_tokens}
    except Exception as e:r={'model':name,'sample':index,'legal':False,'error':type(e).__name__+': '+str(e)[:200]}
    results.append(r);print(json.dumps(r),flush=True)
  await asyncio.gather(*(one(name,i+1) for name in MODELS for i in range(4)))
 summary={name:{'samples':4,'actions':dict(Counter(r.get('action') for r in results if r['model']==name)),'legal':sum(r['legal'] for r in results if r['model']==name)} for name in MODELS};out={'scope':'Exact visible river decision replay, selection only, no oracle-card labels or training use. Call198into202 requires49.5%equity; no legal raise remains against the matched all-in.','models':MODELS,'summary':summary,'results':results};(ROOT/'results.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
asyncio.run(run())
