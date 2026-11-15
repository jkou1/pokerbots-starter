"""Fresh64 checkpoint selection from actual unclipped native artifacts and cleanup logs."""
import hashlib,json,os,re,statistics
from pathlib import Path
from ac2.sdk import Client
from vals_tools.cleanup_score import cleanup_protocol,aggregate_cleanup_protocol
from vals_tools.game_score import bootstrap
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/late-grpo-fresh64-v1';manifest=json.loads((ROOT/'manifest.json').read_text());receipt=json.loads((ROOT/'receipt.json').read_text());task_meta=dict(zip(receipt['task_ids'],manifest['task_metadata'],strict=True));by_seed={row['seed']:row for row in manifest['task_metadata']};c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);runs={}
for label,meta in receipt['evaluations'].items():
 out=ROOT/label;out.mkdir(exist_ok=True);cache=out/'native-artifacts.json'
 if cache.exists():
  run=json.loads(cache.read_text());assert run['eval_id']==meta['eval_id'] and run['checkpoint']==meta['checkpoint']
 else:
  live=c.eval.get(meta['eval_id']);scores=c.analytics.scores(run_ids=[meta['eval_id']]).to_records();spans=c.analytics.spans(run_ids=[meta['eval_id']]).select('output','attributes').filter(name='grade').to_records();arts={}
  for span in spans:
   try:attrs=json.loads(span['attributes'])if isinstance(span['attributes'],str)else span['attributes'];output=json.loads(span['output'])if isinstance(span['output'],str)else span['output'];arts[attrs['agent_trace_id']]=output.get('artifacts',{})
   except(ValueError,TypeError,KeyError):continue
  rows={}
  for score in scores:
   tid=score['datapoint_id'];assert tid in task_meta;art=arts.get(score['agent_trace_id'],{});rows[tid]=task_meta[tid]|{'ev_bb':art.get('ev_bb'),'realized_bb':art.get('realized_bb'),'decisions':art.get('policy_decisions'),'invalid_decisions':art.get('policy_format_errors'),'full_artifacts':art}
  run=meta|{'status':live.status,'job_id':live.job_id,'tasks':rows}
  if live.status=='succeeded'and len(rows)==64 and all(row['ev_bb']is not None for row in rows.values()):cache.write_text(json.dumps(run,indent=2)+'\n')
 runs[label]=run
job_labels={run['job_id']:label for label,run in runs.items()};protocol_rows={label:[]for label in runs};sources={label:[]for label in runs}
for path in Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs').glob('*.json'):
 try:
  raw=path.read_bytes();match=re.search(rb'"relay_job_id"\s*:\s*"([^"]+)"',raw)
  if not match or match[1].decode()not in job_labels:continue
  label=job_labels[match[1].decode()];log=json.loads(raw)
  if not log.get('complete'):continue
  seed=log['session_info']['seed'];assert seed in by_seed and seed not in {row['seed']for row in protocol_rows[label]};seat='seat'+str(by_seed[seed]['policy_seat']);cleanups=[h['cleanup']for h in log.get('private',{}).get(seat,{}).get('hands',{}).values()if h.get('cleanup')];protocol_rows[label].append({'seed':seed,'cleanup_protocol':cleanup_protocol(cleanups)});out=ROOT/label/'raw';out.mkdir(exist_ok=True);(out/path.name).write_bytes(raw);sources[label].append({'path':str(path),'seed':seed,'sha256':hashlib.sha256(raw).hexdigest()})
 except(OSError,ValueError):continue
report={'scope':'Fresh64 single-hand selection only, with32ad74/32base20. Unclipped official artifact EV, sidepots may fall back to realized. Not carried-stack quality, Arena rating or statistical proof; current final release is excluded.','dataset':manifest['dataset'],'runs':{},'comparisons':{}}
for label,run in runs.items():
 rows=list(run['tasks'].values());ev=[x['ev_bb']for x in rows if x['ev_bb']is not None];decisions=sum(x['decisions']or 0 for x in rows);invalid=sum(x['invalid_decisions']or 0 for x in rows);report['runs'][label]={k:run[k]for k in ['eval_id','inference_id','checkpoint','version','status','job_id'] }|{'graded_tasks':len(rows),'unclipped_ev_coverage':len(ev),'mean_ev_bb':statistics.fmean(ev)if ev else None,'policy_decisions':decisions,'invalid_decisions':invalid,'legal_rate':1-invalid/decisions if decisions else None,'raw_cleanup_games':len(protocol_rows[label]),'cleanup_protocol':aggregate_cleanup_protocol(protocol_rows[label]),'source_manifest':sources[label]}
 if label=='step20'or'step20'not in runs:continue
 base=runs['step20']['tasks'];common=sorted(base.keys()&run['tasks'].keys());diffs=[run['tasks'][tid]['ev_bb']-base[tid]['ev_bb']for tid in common if base[tid]['ev_bb']is not None and run['tasks'][tid]['ev_bb']is not None];strata={}
 for opp in manifest['opponents']:
  values=[run['tasks'][tid]['ev_bb']-base[tid]['ev_bb']for tid in common if task_meta[tid]['opponent_stratum']==opp and base[tid]['ev_bb']is not None and run['tasks'][tid]['ev_bb']is not None];strata[opp]={'pairs':len(values),'mean_gain_bb':statistics.fmean(values)if values else None,'ci95':bootstrap(values)}
 report['comparisons'][label]={'paired_tasks':len(diffs),'mean_gain_bb':statistics.fmean(diffs)if diffs else None,'ci95':bootstrap(diffs),'opponent_strata':strata,'scope':'Complete64paired EV and manual protocol inspection required before advancing; no candidate selected from partial results.'}
(ROOT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='runs'}|{'runs':{k:{x:y for x,y in v.items()if x!='source_manifest'}for k,v in report['runs'].items()}},indent=2))
