"""Complete24 approved no-SAYcontrols, reusefirst4withoutduplicate."""
import asyncio,json,os,time
from pathlib import Path
import httpx
from ac2.sdk import Client
from pokerbots_working_client import preflight_identity
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL
R=Path('data/experiments/dominated-fold-talk-v1');p=R/'controls.json';assert not p.exists(),'No duplicatecontrols';initial=json.loads((R/'calibration.json').read_text());assert initial['status']=='complete'and initial['calls_started']==4;rows=[json.loads(x)for x in(R/'development.jsonl').read_text().splitlines()];victims={'ad74':('infer_af82066205bf','ckpt_ad74c826c9ad'),'base20':('infer_21f395f49bff','ckpt_23b6b6239f26')};c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c)
for mid,ck in victims.values():
 m=c.inference.get(mid);assert m.checkpoint_id==ck and m.version==1 and m.state=='ready'
r={'identity':identity,'calls_started':4,'call_cap':24,'included_in_development96':True,'results':initial['results'],'started_at':time.time()}
def save():tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(p)
async def run():
 sem=asyncio.Semaphore(2)
 async with httpx.AsyncClient(timeout=180)as http:
  async def one(v,mid,row):
   async with sem:
    r['calls_started']+=1;save();start=time.time();out={'victim':v,'inference_id':mid,'state_id':row['id'],'arm':'none'}
    try:
     complete=relay_completion(http,GATEWAY_URL,os.environ['AC2_API_KEY'],with_preset({'preset':'event','model_label':mid,'temperature':0.0}),retries=0);reply=await asyncio.wait_for(complete(row['variants']['none']),180);calls=reply.tool_calls;args=json.loads(calls[0]['function']['arguments'])if len(calls)==1 else{};action=args.get('action');valid=len(calls)==1 and calls[0]['function']['name']=='submit_action'and action in['fold','call','raise']and not reply.truncated and(action!='raise'or type(args.get('amount'))is int and 4<=args['amount']<=200);out.update(valid=valid,action=action,tool_calls=calls,truncated=reply.truncated,reasoning=reply.reasoning,text=reply.text,tokens=reply.out_tokens)
    except Exception as e:out.update(valid=False,error=type(e).__name__+': '+str(e)[:300])
    out['seconds']=time.time()-start;r['results'].append(out);save();print(v,row['id'],out.get('action'),out['valid'],flush=True)
  await asyncio.gather(*(one(v,mid,row)for v,(mid,ck)in victims.items()for row in rows if not any(x['victim']==v and x['state_id']==row['id']for x in initial['results'])))
 r.update(status='complete',all_real_tools_valid=all(x['valid']for x in r['results']),no_full_matrix_launched=True);save()
save();asyncio.run(run())
