"""Root-authorized sixteen paired BASE probes; no training and no fabricated replies."""
import argparse,asyncio,contextvars,copy,hashlib,json,os,sys,time
from pathlib import Path
import httpx
from dotenv import dotenv_values
from ac2.sdk import Client
from poker_harness.completions import relay_completion,with_preset,GATEWAY_URL,_tools
from poker_harness.training import action_args,betting_action
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.collect_policy import trace_reply
from vals_tools.pete_eval import legal_prediction
sys.path.insert(0,'/tmp');from pokerbots_working_client import preflight_identity
parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);parser.add_argument('--ready-receipt',type=Path,required=True);args=parser.parse_args();R=Path(__file__).resolve().parent;os.umask(0o077);(R/'raw').mkdir(exist_ok=True);manifest=json.loads((R/'manifest.json').read_text());fit=json.loads((R/'tokenfit.json').read_text());assert hashlib.sha256((R/'cases.jsonl').read_bytes()).hexdigest()==manifest['cases_sha256']==fit['source_cases_sha256'];rows=[json.loads(l)for l in(R/'cases.jsonl').open()];assert len(rows)==16;ready=json.loads(args.ready_receipt.read_text());assert ready['ready_verified']and ready['inference_id']==args.model
lock=R/'probe-policy.json'
if lock.exists():raise SystemExit('Calibration already attempted; no duplicate/replacement calls')
key=dotenv_values('/Users/lance/Documents/pokerbots-starter/.env')['AC2_API_KEY'];c=Client(project='vals-hackathon',api_key=key);identity=preflight_identity(c);info=c.inference.get(args.model);assert info.model==info.served_model=='Qwen/Qwen3.6-35B-A3B'and info.checkpoint_id is None and info.version==1
params=with_preset({'preset':'event','model_label':args.model,'temperature':1.0,'max_completion_tokens':5000,'submit_fields':['action','amount','say']});assert params['max_completion_tokens']==5000;assert[{'type':x['type'],**x['function']}for x in _tools(params)]==json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text());policy={'started_epoch':time.time(),'model':args.model,'catalog_model':info.model,'checkpoint':None,'version':1,'identity':identity,'root_32call_GO':True,'cases_sha256':manifest['cases_sha256'],'pairs':16,'logical_call_cap':32,'temperature_both':1,'reply_cap_both':5000,'concurrency':4,'retries':0,'wall_cap_seconds':900,'gate':manifest['frozen_gate'],'case_or_hint_changes_after_outputs':False,'no_native_training_authorized':True};lock.write_text(json.dumps(policy,indent=2)+'\n');ctx=contextvars.ContextVar('case_arm');wire={}
async def run():
 results=[None]*16;sem=asyncio.Semaphore(4);calls=0
 def save(status):
  p=R/'raw/results.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps({'status':status,'logical_calls_started':calls,'results':results},indent=2)+'\n');tmp.replace(p);(R/'progress.json').write_text(json.dumps({'status':status,'logical_calls_started':calls,'completed_pairs':sum(x is not None for x in results),'all_requests_drained':status=='complete'},indent=2)+'\n')
 async def capture(response):
  await response.aread();i,arm=ctx.get();(R/f'raw/case{i}-{arm}-request.json').write_bytes(response.request.content);(R/f'raw/case{i}-{arm}-response.json').write_bytes(response.content);wire[(i,arm)]={'request':json.loads(response.request.content),'response':json.loads(response.content),'status':response.status_code}
 async with httpx.AsyncClient(timeout=180,event_hooks={'response':[capture]})as http:
  complete=relay_completion(http,GATEWAY_URL,key,params,retries=0)
  async def one(i,row):
   nonlocal calls
   async with sem:
    p=row['original_input'];assert hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()==row['original_input_sha256'];record={'case':i,'source_group':row['source_provenance']['scenario_group'],'source_index':row['source_provenance']['source_index'],'target':row['original_provider_scaled_target'],'arms':{}}
    for arm in ['unhinted','hinted']:
     inputs=copy.deepcopy(p)
     if arm=='hinted':inputs[0]['content']+='\n\n'+row['teacher_system_only_hint']
     assert inputs[1:]==p[1:];token=ctx.set((i,arm));calls+=1;started=time.monotonic();save('running')
     try:
      reply=await asyncio.wait_for(complete(inputs),180);w=wire[(i,arm)];choice=w['response']['choices'][0];finish=choice.get('finish_reason');items=[x.model_dump(mode='json',exclude_none=True)for x in trace_reply(reply)];message=choice['message'];assert message.get('reasoning_content')==reply.reasoning and message.get('content')==reply.text and (message.get('tool_calls')or[])==reply.tool_calls
      record['arms'][arm]={'runtime_reply_exact':items,'reasoning':reply.reasoning,'text':reply.text,'tool_calls':reply.tool_calls,'legal':False,'exact_provider_action_amount':False,'truncated':reply.truncated,'finish_reason':finish,'genuine_single_correct_tool':len(reply.tool_calls)==1,'complete':not reply.truncated and finish in ['tool_calls','stop'],'out_tokens':reply.out_tokens,'usage':w['response'].get('usage'),'response_id':w['response'].get('id'),'seconds':time.monotonic()-started,'request_messages_equal_expected':w['request']['messages']==inputs}
      rawargs=action_args(reply);action=betting_action(rawargs);legal=bool(legal_prediction({'legal':row['facts']['legal']},action));record['arms'][arm].update(raw_arguments=rawargs,normalized_action=action,legal=legal,exact_provider_action_amount=legal and action==row['original_provider_scaled_target'])
     except Exception as e:
      w=wire.get((i,arm),{});record['arms'].setdefault(arm,{});record['arms'][arm].update({'error':type(e).__name__+':'+str(e)[:300],'legal':False,'exact_provider_action_amount':False,'complete':False,'genuine_single_correct_tool':False,'seconds':time.monotonic()-started,'wire_captured':bool(w)})
     finally:ctx.reset(token)
    results[i]=record;save('running');print('paircomplete',i,'pairs',sum(x is not None for x in results),'calls',calls,flush=True)
  try:
   async with asyncio.timeout(900):await asyncio.gather(*(one(i,row)for i,row in enumerate(rows)))
  except TimeoutError:save('timeout');raise
 save('complete');counts={a:sum(bool(x and x['arms'][a].get('exact_provider_action_amount'))for x in results)for a in ['unhinted','hinted']};allteacher=all(x['arms']['hinted'].get('legal')and x['arms']['hinted'].get('complete')and x['arms']['hinted'].get('genuine_single_correct_tool')for x in results);summary={'cases_intention_to_treat':16,'logical_calls':32,'model':args.model,'catalog_model':info.model,'version':1,'counts_exact_normalized_action_amount':counts,'gain':counts['hinted']-counts['unhinted'],'all16_hinted_genuine_legal_complete':allteacher,'gate_pass':counts['hinted']>=14 and counts['hinted']-counts['unhinted']>=4 and allteacher,'all_requests_drained':True,'agreement_rule':'Existingbetting_action(action_args(reply));amountonlyforbet/raise,nonaggressiveamountignored','no_rewrites_retries_replacement_cases':True,'native_training_GO':False};(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
asyncio.run(run())
