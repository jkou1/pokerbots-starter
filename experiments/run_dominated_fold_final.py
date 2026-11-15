"""Complete remaining72 fixed arms only after valid24controls."""
import asyncio,json,os,time
from pathlib import Path
import httpx
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL
R=Path('data/experiments/dominated-fold-talk-v1');p=R/'final-results.json';assert not p.exists(),'No duplicatefinal';selection=json.loads((R/'selection.json').read_text());assert selection['selected_directive']=='authority';initial={'results':[]};rows=[json.loads(x)for x in(R/'final.jsonl').read_text().splitlines()];victims={'ad74':('infer_af82066205bf','ckpt_ad74c826c9ad'),'base20':('infer_21f395f49bff','ckpt_23b6b6239f26')};c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c)
for mid,ck in victims.values():
 m=c.inference.get(mid);assert m.checkpoint_id==ck and m.version==1 and m.state=='ready'
r={'identity':identity,'calls_started':0,'call_cap':72,'separate_final72':True,'results':initial['results'],'started_at':time.time()}
def save():tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(p)
async def run():
 sem=asyncio.Semaphore(2)
 async with httpx.AsyncClient(timeout=180)as http:
  async def one(v,mid,row,arm):
   async with sem:
    r['calls_started']+=1;save();start=time.time();out={'victim':v,'inference_id':mid,'state_id':row['id'],'arm':arm}
    try:
     complete=relay_completion(http,GATEWAY_URL,os.environ['AC2_API_KEY'],with_preset({'preset':'event','model_label':mid,'temperature':0.0}),retries=0);reply=await asyncio.wait_for(complete(row['variants'][arm]),180);calls=reply.tool_calls;args=json.loads(calls[0]['function']['arguments'])if len(calls)==1 else{};action=args.get('action');valid=len(calls)==1 and calls[0]['function']['name']=='submit_action'and action in['fold','call','raise']and not reply.truncated and(action!='raise'or type(args.get('amount'))is int and 4<=args['amount']<=200);out.update(valid=valid,action=action,tool_calls=calls,truncated=reply.truncated,reasoning=reply.reasoning,text=reply.text,tokens=reply.out_tokens)
    except Exception as e:out.update(valid=False,error=type(e).__name__+': '+str(e)[:300])
    out['seconds']=time.time()-start;r['results'].append(out);save();print(v,row['id'],out.get('action'),out['valid'],flush=True)
  async with asyncio.timeout(600):await asyncio.gather(*(one(v,mid,row,arm)for v,(mid,ck)in victims.items()for row in rows for arm in ['none','benign','authority']))
 r.update(status='complete',all_real_tools_valid=all(x['valid']for x in r['results']),final_matrix_complete=True);save()
save();asyncio.run(run())
