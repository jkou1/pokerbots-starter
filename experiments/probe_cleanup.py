"""Replay actual own held-out cleanup histories under official cleanup limits."""
import argparse,asyncio,json,os,time
from pathlib import Path
import httpx
from poker_harness.completions import relay_completion,with_preset,cleanup_params,GATEWAY_URL
ROOT=Path(__file__).resolve().parent.parent

def chat_history(items):
 messages=[]
 for item in items:
  typ=item.get('type')
  if typ=='message':messages.append({'role':item['role'],'content':item.get('content','')})
  elif typ=='function_call':
   if not messages or messages[-1]['role']!='assistant':messages.append({'role':'assistant','content':''})
   messages[-1].setdefault('tool_calls',[]).append({'id':item['call_id'],'type':'function','function':{'name':item['name'],'arguments':item['arguments']}})
  elif typ=='function_call_output':messages.append({'role':'tool','tool_call_id':item['call_id'],'content':item['output']})
  elif typ=='reasoning':raise ValueError('Unexpected historical reasoning; preserve source before conversion')
  else:raise ValueError('Unknown runtime item '+str(typ))
 return messages

async def run(a):
 rows=[json.loads(x) for x in (ROOT/'data/experiments/cleanup-stress-select-v1/select.jsonl').read_text().splitlines()];results=[None]*len(rows);sem=asyncio.Semaphore(2);p=ROOT/f'data/experiments/cleanup-stress-results/{a.name}.json';p.parent.mkdir(parents=True,exist_ok=True)
 def save(status):p.write_text(json.dumps({'status':status,'model':a.model,'results':results,'valid':sum(bool(x and x.get('valid')) for x in results),'completed':sum(x is not None for x in results)},indent=2))
 async with httpx.AsyncClient(timeout=120) as c:
  complete=relay_completion(c,GATEWAY_URL,os.environ['AC2_API_KEY'],cleanup_params(with_preset({'preset':'event','model_label':a.model,'submit_fields':['action','amount']})))
  async def one(i,row):
   async with sem:
    started=time.monotonic()
    try:
     reply=await asyncio.wait_for(complete(chat_history(row['messages'])),timeout=180);calls=[x for x in reply.tool_calls if x['function']['name']=='update_scratchpad'];payload=json.loads(calls[0]['function']['arguments']) if len(calls)==1 else {};contents=payload.get('contents');valid=isinstance(contents,str) and len(contents)<=5000 and not reply.truncated
     result={'valid':valid,'characters':len(contents) if isinstance(contents,str) else None,'tokens':reply.out_tokens,'truncated':reply.truncated,'tool_calls':reply.tool_calls,'contents':contents,'reasoning':reply.reasoning,'text':reply.text}
    except Exception as e:result={'valid':False,'error':type(e).__name__+': '+str(e)}
    results[i]=result|{'source':row['provenance'],'source_model':row['model'],'source_characters':row['observed_contents_characters'],'seconds':round(time.monotonic()-started,2)};save('running');print(json.dumps({'completed':sum(x is not None for x in results),'valid':sum(bool(x and x.get('valid')) for x in results),'last_characters':result.get('characters')}),flush=True)
  try:
   async with asyncio.timeout(300):await asyncio.gather(*(one(i,row) for i,row in enumerate(rows)))
  except TimeoutError:save('timed_out');print('cleanup stress timed out after300seconds',flush=True);return
 save('complete')
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--name',required=True);asyncio.run(run(p.parse_args()))
