"""Frozen LOCAL ad74 SELECT/retention baseline, retries0, no FINAL or GPU jobs."""
import asyncio,json,copy,os,sys,re,time,hashlib,collections
from pathlib import Path
import httpx
from dotenv import dotenv_values
sys.path.insert(0,'/tmp');from pokerbots_working_client import preflight_identity
from ac2.sdk import Client
from poker_harness.completions import relay_completion,with_preset,cleanup_params,GATEWAY_URL,_tools
from poker_harness.training import action_args,betting_action
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.pete_eval import imitation_metrics
from vals_tools.collect_policy import trace_reply
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval');P=R.parent/'pete-postflop-v1';O=R/'parent-baseline';O.mkdir(exist_ok=True);(O/'raw').mkdir(exist_ok=True);os.umask(0o077);MODEL='infer_af82066205bf'
if (O/'lock.json').exists():raise SystemExit('Baseline already attempted; do not duplicate')
train=[json.loads(l)for l in(R.parent/'pokerbench-v4/preflop-anchors.jsonl').open()];pre=[json.loads(l)for l in(P/'preflop-select.jsonl').open()];assert not{x['provenance']['match_id']for x in train}&{x['provenance']['match_id']for x in pre};assert not{x['deal_identity']for x in train}&{x['deal_identity']for x in pre};pb=[json.loads(l)for l in(R/'select.jsonl').open()]
for row in pb:
 t=row['input'][1]['content'];seats=['UTG','HJ','CO','BTN','SB','BB'];st={s:200 for s in seats};be={s:0 for s in seats};be['SB']=1;be['BB']=2;st['SB']-=1;st['BB']-=2;hero=re.search(r'your position is (UTG|HJ|CO|BTN|SB|BB)',t)[1];last=2
 for n,section in enumerate(re.split(r'The flop comes|The turn comes|The river comes',t)):
  if n:be={s:0 for s in seats}
  last=2
  for seat,a,num in re.findall(r'\b(UTG|HJ|CO|BTN|SB|BB) (raise|bet|call|check|fold)(?: (\d+))?',section):
   old=max(be.values())
   if a in ['raise','bet']:
    total=int(num);commit=total-be[seat]
    if total-old>=last:last=total-old
   elif a=='call':commit=min(st[seat],old-be[seat])
   else:continue
   st[seat]-=commit;be[seat]+=commit
 call=min(st[hero],max(be.values())-be[hero]);maximum=st[hero]+be[hero];minimum=min(maximum,max(be.values())+last);row['legal']={'can_fold':True,'can_check':call==0,'call_amount':call,'raise_type':'raise'if max(be.values())else'bet','min_raise_to':minimum,'max_raise_to':maximum};row['position']=hero
cleanupfile=E/'data/experiments/cleanup-stress-select-v1/select.jsonl';cleanup=[json.loads(l)for l in cleanupfile.open()];key=dotenv_values('/Users/lance/Documents/pokerbots-starter/.env')['AC2_API_KEY'];c=Client(project='vals-hackathon',api_key=key);identity=preflight_identity(c);info=c.inference.get(MODEL);assert info.checkpoint_id=='ckpt_ad74c826c9ad';original41=[json.loads(l)for l in(R.parent/'pokerbench-v4/select.jsonl').open()];assert all(x['input']==y['input']and x['target']==y['target']and x['provenance']==y['provenance']for x,y in zip(pb[:41],original41));oldlock=json.loads((R.parent/'pokerbench-v4/parent-baseline/lock.json').read_text());assert oldlock['model']==MODEL and oldlock['checkpoint']==info.checkpoint_id and oldlock['version']==info.version;assert hashlib.sha256((P/'preflop-select.jsonl').read_bytes()).hexdigest()==oldlock['input_files_sha256'][str(P/'preflop-select.jsonl')];assert hashlib.sha256(cleanupfile.read_bytes()).hexdigest()==oldlock['input_files_sha256'][str(cleanupfile)];lock={'parent_reuse_input_checkpoint_version_proved':True,'fresh_calls_only':95,'reused_original41_pre354_cleanup10':True,'model':MODEL,'checkpoint':info.checkpoint_id,'version':info.version,'identity':identity,'started_utc_seconds':time.time(),'wall_cap_seconds':900,'retries':0,'concurrency':4,'temperature':0,'input_files_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in [R/'select.jsonl',P/'preflop-select.jsonl',cleanupfile]},'preflop_train_match_and_deal_overlap':0,'local_imitation_not_ev':True,'no_final':True};(O/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
params=with_preset({'preset':'event','model_label':MODEL,'temperature':0.0,'submit_fields':['action','amount','say']});assert [{'type':x['type'],**x['function']}for x in _tools(params)]==json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text())
oldrequests=[json.loads(f.read_bytes())for f in(R.parent/'pokerbench-v4/parent-baseline/raw').glob('http-*-request.json')];wireproof=[]
for row in original41:
 matched=[x for x in oldrequests if x.get('messages')==row['input']];assert len(matched)==1;b=matched[0];assert b['model']==MODEL and b['tools']==_tools(params) and b['temperature']==0 and b['max_completion_tokens']==params['max_completion_tokens']and b['chat_template_kwargs']=={'enable_thinking':True};wireproof.append(hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest())
(O/'cached41-wire-reuse-proof.json').write_text(json.dumps({'cases':41,'exact_messages_tools_checkpoint_version_temperature_budget_match':True,'request_sha256':wireproof},indent=2)+'\n')
def chat(items):
 out=[]
 for x in items:
  if x['type']=='message':out.append({'role':x['role'],'content':x.get('content','')})
  elif x['type']=='function_call':
   if not out or out[-1]['role']!='assistant':out.append({'role':'assistant','content':''})
   out[-1].setdefault('tool_calls',[]).append({'id':x['call_id'],'type':'function','function':{'name':x['name'],'arguments':x['arguments']}})
  elif x['type']=='function_call_output':out.append({'role':'tool','tool_call_id':x['call_id'],'content':x['output']})
  else:raise ValueError('Unsupported history; no fabricated conversion')
 return out
async def run():
 async def capture(resp):
  await resp.aread();name=str(time.time_ns());(O/f'raw/http-{name}-response.json').write_bytes(resp.content);(O/f'raw/http-{name}-request.json').write_bytes(resp.request.content)
 async with httpx.AsyncClient(timeout=180,event_hooks={'response':[capture]})as http:
  async def stage(name,rows,is_cleanup=False):
   sem=asyncio.Semaphore(4);results=[None]*len(rows);complete=relay_completion(http,GATEWAY_URL,key,cleanup_params(params)if is_cleanup else params,retries=0)
   def save(status):
    (O/f'raw/{name}.json').write_text(json.dumps({'status':status,'results':results},indent=2)+'\n');(O/'progress.json').write_text(json.dumps({'stage':name,'status':status,'completed':sum(x is not None for x in results),'total':len(rows)},indent=2)+'\n')
   async def one(i,row):
    async with sem:
     try:
      reply=await asyncio.wait_for(complete(chat(row['messages'])if is_cleanup else row['input']),180);record={'runtime_reply':[x.model_dump(mode='json')for x in trace_reply(reply)],'tokens':reply.out_tokens,'truncated':reply.truncated}
      if is_cleanup:
       calls=reply.tool_calls;args=json.loads(calls[0]['function']['arguments'])if len(calls)==1 else{};contents=args.get('contents');record.update(valid=len(calls)==1 and calls[0]['function']['name']=='update_scratchpad'and set(args)=={'contents'}and isinstance(contents,str)and 0<len(contents)<=5000 and not reply.truncated,characters=len(contents)if isinstance(contents,str)else None,wrong_tool_calls=sum(x['function']['name']!='update_scratchpad'for x in calls))
      else:record['action']=betting_action(action_args(reply))
     except Exception as e:record={'action':{},'valid':False,'error':type(e).__name__+':'+str(e)[:200]}
     results[i]=record;save('running')
   await asyncio.gather(*(one(i,row)for i,row in enumerate(rows)));save('complete');summary={'examples':len(rows),'valid':sum(x.get('valid',False)for x in results),'overlong':sum((x.get('characters')or 0)>5000 for x in results),'wrong_tool_calls':sum(x.get('wrong_tool_calls',0)for x in results)}if is_cleanup else imitation_metrics(rows,[x['action']for x in results]);(O/f'{name}-summary.json').write_text(json.dumps({'label':'LOCAL diagnostic, not poker EV','model':MODEL,'checkpoint':info.checkpoint_id,'summary':summary},indent=2)+'\n');print(name,json.dumps(summary),flush=True)
  async with asyncio.timeout(900):
   await stage('new-select95',pb[41:])
  olddir=R.parent/'pokerbench-v4/parent-baseline';cached=json.loads((olddir/'raw/pokerbench-select41.json').read_text())['results'];fresh=json.loads((O/'raw/new-select95.json').read_text())['results'];assert len(cached)==41 and len(fresh)==95;combined=cached+fresh;summary=imitation_metrics(pb,[x['action']for x in combined]);(O/'raw/select136.json').write_text(json.dumps({'status':'complete','results':combined},indent=2)+'\n');(O/'select136-summary.json').write_text(json.dumps({'label':'LOCAL imitation, not poker EV','model':MODEL,'checkpoint':info.checkpoint_id,'summary':summary,'cached41_reused_with_exact_wireproof':True,'fresh_policy_calls':95},indent=2)+'\n');print('select136',json.dumps(summary),flush=True)
 (O/'complete.json').write_text(json.dumps({'complete':True,'calls':95,'all_requests_drained':True,'no_retries':True,'no_final':True},indent=2)+'\n')
asyncio.run(run())
