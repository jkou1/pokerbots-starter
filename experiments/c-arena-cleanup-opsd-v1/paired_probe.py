"""Root-approved fixed10 paired OWN10 smoke; no training or fabricated replies."""
import argparse,asyncio,copy,hashlib,json,os,sys,time
from pathlib import Path
import httpx
from dotenv import dotenv_values
sys.path.insert(0,'/tmp');from pokerbots_working_client import preflight_identity
from ac2.sdk import Client
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.collect_policy import trace_reply
from poker_harness.completions import relay_completion,with_preset,cleanup_params,GATEWAY_URL,_tools
R=Path(__file__).resolve().parent;os.umask(0o077);MODEL='infer_42df4eab0ad2';rows=[json.loads(l)for l in(R/'locked-first10-contexts.jsonl').open()];assert len(rows)==10
fit=json.loads((R/'locked-first10-tokenfit.json').read_text());assert fit['source_jsonl_sha256']==hashlib.sha256((R/'locked-first10-contexts.jsonl').read_bytes()).hexdigest()
policy={'locked_at':time.time(),'model':MODEL,'checkpoint':'ckpt_95bc5ed22ed8','cases':10,'logical_model_call_cap':20,'concurrency':2,'temperature':0.0,'cleanup_reply_budget_each_arm':10000,'hinted_min_useful_valid':8,'hinted_min_gain_over_unhinted':3,'maximum_note_characters':1500,'all_cases_intention_to_treat':True,'no_hint_rewrites_or_replacement_cases':True,'original_source_sha256':fit['source_jsonl_sha256'],'hint_sha256':[hashlib.sha256(c['teacher_hint'].encode()).hexdigest()for c in rows]}
lock=R/'paired-first10-policy.json'
if lock.exists():raise SystemExit('Paired smoke already attempted; no duplicate calls')
lock.write_text(json.dumps(policy,indent=2)+'\n')
key=dotenv_values('/Users/lance/Documents/pokerbots-starter/.env')['AC2_API_KEY'];client=Client(project='vals-hackathon',api_key=key);preflight_identity(client);info=client.inference.get(MODEL);assert info.checkpoint_id=='ckpt_95bc5ed22ed8'and info.version==1
params=cleanup_params(with_preset({'preset':'event','model_label':MODEL,'temperature':0.0,'submit_fields':['action','amount','say']}));assert params['max_completion_tokens']==10000
canonical=json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text());assert [{'type':x['type'],**x['function']}for x in _tools(params)]==canonical

def chat(items):
 messages=[]
 for x in items:
  if x['type']=='message':messages.append({'role':x['role'],'content':x.get('content','')})
  elif x['type']=='function_call':
   if not messages or messages[-1]['role']!='assistant':messages.append({'role':'assistant','content':''})
   messages[-1].setdefault('tool_calls',[]).append({'id':x['call_id'],'type':'function','function':{'name':x['name'],'arguments':x['arguments']}})
  elif x['type']=='function_call_output':messages.append({'role':'tool','tool_call_id':x['call_id'],'content':x['output']})
  else:raise ValueError('Unsupported original history; no quote/clean fallback')
 return messages

async def run():
 results=[None]*10;sem=asyncio.Semaphore(2);calls=0
 def save(status):
  out={'status':status,'policy':policy,'logical_calls_started':calls,'cases_completed':sum(x is not None for x in results),'results':results};p=R/'raw/paired-first10-results.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(p);(R/'paired-first10-progress.json').write_text(json.dumps({k:v for k,v in out.items()if k not in ['results','policy']},indent=2)+'\n')
 async with httpx.AsyncClient(timeout=180)as http:
  complete=relay_completion(http,GATEWAY_URL,key,params,retries=0)
  async def one(i,c):
   nonlocal calls
   async with sem:
    original=json.loads(c['original_input_json_exact']);assert original[0]['role']=='system';record={'source_span_id':c['span_id'],'source_match_id':c['source_match_id'],'original_input_json_exact':c['original_input_json_exact'],'original_input_sha256':c['original_input_sha256'],'hint':c['teacher_hint'],'arms':{}}
    for arm in ['unhinted','hinted']:
     inputs=copy.deepcopy(original)
     if arm=='hinted':inputs[0]['content']+='\n\n'+c['teacher_hint']
     calls+=1;started=time.time();save('running')
     try:
      reply=await asyncio.wait_for(complete(chat(inputs)),timeout=180);items=[x.model_dump(mode='json')for x in trace_reply(reply)];record['arms'][arm]={'runtime_items_exact':items,'reasoning':reply.reasoning,'text':reply.text,'tool_calls':reply.tool_calls,'truncated':reply.truncated,'out_tokens':reply.out_tokens,'seconds':time.time()-started,'input_runtime_items':inputs,'teacher_only_system_mutation':arm=='hinted'}
     except Exception as e:record['arms'][arm]={'error':type(e).__name__+': '+str(e)[:300],'seconds':time.time()-started}
    results[i]=record;save('running');print('completed_pair',i+1,'total_complete',sum(x is not None for x in results),'calls',calls,flush=True)
  try:
   async with asyncio.timeout(600):await asyncio.gather(*(one(i,c)for i,c in enumerate(rows)))
  except TimeoutError:save('timed_out');raise
 save('complete');print('all10pairs_complete20calls',flush=True)
asyncio.run(run())
