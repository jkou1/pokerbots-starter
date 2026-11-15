"""Repeat an observed held-out invalid-enum decision without changing its prompt."""
import argparse,asyncio,json,os
from pathlib import Path
import httpx
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL
ROOT=Path(__file__).resolve().parent.parent
async def run(a):
 r=json.loads((ROOT/'data/experiments/incumbent-enum-regression.json').read_text());messages=[{'role':i['role'],'content':i['content']} for i in r['input'] if i['type']=='message'];out=[]
 async with httpx.AsyncClient(timeout=300) as c:
  complete=relay_completion(c,GATEWAY_URL,os.environ['AC2_API_KEY'],with_preset({'preset':'event','model_label':a.model,'submit_fields':['action','amount']}))
  for _ in range(a.repeats):
   rep=await complete(messages)
   try:
    calls=[x for x in rep.tool_calls if x['function']['name']=='submit_action'];args=json.loads(calls[0]['function']['arguments']) if len(calls)==1 else {};act=args.get('action');legal=not rep.truncated and (act in ['fold','call'] or (act=='raise' and type(args.get('amount')) is int and 12<=args['amount']<=200))
   except Exception as e:args={'error':str(e)};legal=False
   out.append({'legal':legal,'args':args,'tokens':rep.out_tokens,'truncated':rep.truncated,'tool_calls':rep.tool_calls});print(json.dumps(out[-1]),flush=True)
 p=ROOT/f'data/experiments/enum-probes/{a.name}.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'model':a.model,'repeats':a.repeats,'legal':sum(x['legal'] for x in out),'results':out},indent=2))
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--name',required=True);p.add_argument('--repeats',type=int,default=4);asyncio.run(run(p.parse_args()))
