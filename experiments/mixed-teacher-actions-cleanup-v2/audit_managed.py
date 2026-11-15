"""Read existing monitor caches only: actual control token share and tool CE."""
import argparse,collections,gzip,hashlib,json,re,sys,time,os
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'/Users/lance/Documents/pokerbots-pokerbench/experiments/pete-postflop-v1')
from action_ce import token_ce
R=Path(__file__).resolve().parent

def audit():
 provenance=json.loads((R/'task-provenance-map.json').read_text());state=json.loads((R/'monitor-state.json').read_text());steps={};total=collections.Counter();cleanup_ce=[];tool_ce=[]
 for path in sorted(R.glob('managed-step-*.jsonl.gz')):
  step=path.name.split('-')[2].split('.')[0];counts=collections.Counter();tokens=collections.Counter();ce=[];routes=[]
  with gzip.open(path,'rt') as f:rows=[json.loads(l) for l in f]
  for row in rows:
   p=row['payload'];source=provenance[p['datapoint_id']];kind=source.get('teacher','genuine-own-cleanup');counts[kind]+=1
   mask=p['loss_mask'];assert len(mask)==len(p['sampled_tokens']);tokens[kind]+=sum(x==1 for x in mask)
   text=''.join(p['sampled_tokens'])
   assert text.count('</think>')==1 and text.count('<tool_call>')==1 and text.count('</tool_call>')==1
   route=re.search(r'<function=(submit_action|update_scratchpad)>',text)
   if route:
    value,n=token_ce(p,route.span(1));routes.append({'tool':route[1],'ce':value,'tokens':n})
   if kind=='genuine-own-cleanup':
    m=re.search(r'<parameter=contents>\n(.*?)\n</parameter>',text,re.S)
    if m:
     value,n=token_ce(p,m.span(1));ce.append({'ce':value,'tokens':n})
  total.update(tokens);cleanup_ce+=ce;tool_ce+=routes
  steps[step]={'observed_sequences':len(rows),'expected_batch':128,'full_batch_export':len(rows)==128,'kind_counts':dict(counts),'supervised_target_tokens':dict(tokens),'cleanup_target_token_fraction':tokens['genuine-own-cleanup']/sum(tokens.values()) if tokens else None,'cleanup_contents_ce':sum(x['ce'] for x in ce)/len(ce) if ce else None,'tool_route_ce':{tool:sum(x['ce'] for x in routes if x['tool']==tool)/sum(x['tool']==tool for x in routes) for tool in {x['tool'] for x in routes}},'sample_cache_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 report={'updated_at':datetime.now(timezone.utc).isoformat(),'watcher_pid':os.getpid(),'train_id':state['run'],'training_updates':state['training_updates'],'actual_managed_steps':steps,'observed_supervised_target_tokens':dict(total),'observed_cleanup_target_token_fraction':total['genuine-own-cleanup']/sum(total.values()) if total else None,'cleanup_contents_ce':sum(x['ce'] for x in cleanup_ce)/len(cleanup_ce) if cleanup_ce else None,'source':'Existing exact managed token caches from monitor; no additional API/model calls','limitations':['Token visualization may be a sampled export of each optimizer batch.','Different minibatches are not fixed validation; token CE is not poker quality.','Cleanup contents CE measures genuine target imitation, not general factual correctness.'],'no_dataset_or_job_mutation':True}
 p=R/'managed-aggregate-audit.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(p);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');args=p.parse_args()
 while True:
  try:
   result=audit();print(result['updated_at'],'steps',len(result['actual_managed_steps']),'updates',result['training_updates'],flush=True)
   if not args.watch or result['training_updates']>=10 and len(result['actual_managed_steps'])>=10:break
  except (OSError,EOFError,ValueError,KeyError) as e:
   if not args.watch:raise
   print(type(e).__name__,str(e)[:120],flush=True)
  if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-11-15T17:00:00+00:00'):break
  time.sleep(30)
