"""Existing four development games only; raw rank/EV/protocol and channel, no FINAL data."""
import hashlib,json,os,re,statistics
from pathlib import Path
from ac2.sdk import Client
from poker_harness.grading import seat_result
from vals_tools.cleanup_score import cleanup_protocol,aggregate_cleanup_protocol
from vals_tools.game_score import bootstrap
R=Path('data/experiments/base-grpo5-development-v1');receipt=json.loads((R/'receipt.json').read_text());baseR=Path('data/experiments/base20-development-v1');baseReceipt=json.loads((baseR/'receipt.json').read_text());baselines=json.loads((baseR/'summary.json').read_text())['runs'];seats={seed:'seat'+str(i)for i,seed in enumerate(baseReceipt['seeds'])};c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);run=c.eval.get(receipt['eval_id']);rows=[];manifest=[];source=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs');(R/'raw').mkdir(exist_ok=True)
for p in source.glob('*.json'):
 try:
  raw=p.read_bytes();job=re.search(rb'"relay_job_id"\s*:\s*"([^"]+)"',raw)
  if not job or job.group(1).decode()!=run.job_id:continue
  log=json.loads(raw)
  if not log.get('complete'):continue
  seed=log['session_info']['seed'];assert seed in seats;seat=seats[seed];result=seat_result(log,[seat]);cleanups=[x['cleanup']for x in log.get('private',{}).get(seat,{}).get('hands',{}).values()if x.get('cleanup')];actions=[a for h in log['hands']for a in h['actions']if a['player']==seat];channel={'legal_real_tool':0,'legal_text_json_fallback':0,'legal_channel_unexposed':0,'invalid':0};talk=[]
  for action in actions:
   response=action.get('model_response',{});invalid=response.get('format_error');channel['invalid'if invalid else'legal_real_tool'if response.get('submitted_by_tool')is True else'legal_text_json_fallback'if response.get('submitted_by_tool')is False else'legal_channel_unexposed']+=1;rawsay=response.get('private',{}).get('say_raw');say=response.get('say')or action.get('say')
   if rawsay or say:talk.append({'say':say,'raw_say':rawsay})
  row={'seed':seed,'seat':seat,'place':log['ranking']['places'][seat],'busted':seat in log.get('eliminated_on_hand',{}),'ev_bb':result.ev_bb,'realized_bb':result.realized_bb,'decisions':result.decisions,'invalid_decisions':result.format_errors,'hands':len(log['hands']),'cleanup_protocol':cleanup_protocol(cleanups),'policy_action_channel':channel,'talk':talk};rows.append(row);(R/'raw'/p.name).write_bytes(raw);manifest.append({'source':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'seed':seed,'relay_job_id':run.job_id})
 except(OSError,json.JSONDecodeError):continue
assert len({x['seed']for x in rows})==len(rows);report={'scope':'4SELECTIONdevelopment30handgames; smallsample,notproof/convergence. CachedC/RL20 same4deals/base20. UnsupportedsidepotEVfallbacklabelpreservedinraw. NoFINALsourceoroutcomeuse.','eval_id':run.eval_id if hasattr(run,'eval_id')else receipt['eval_id'],'job_id':run.job_id,'status':run.status,'planned_games':4,'completed_games':len(rows),'games':sorted(rows,key=lambda x:x['seed']),'source_manifest':manifest,'paired':{},'workplace_review_pending':True,'factual_memory_audit':'diagnosticownedbysft_data; noclaimedimprovement'}
for label in['incumbent','rl20']:
 baseline={x['seed']:x for x in baselines[label]['games']};common=sorted(set(baseline)&{x['seed']for x in rows});new={x['seed']:x for x in rows};rank=[baseline[s]['place']-new[s]['place']for s in common];ev=[new[s]['ev_bb']-baseline[s]['ev_bb']for s in common];report['paired'][label]={'games':len(common),'mean_rank_gain':statistics.fmean(rank)if rank else None,'rank_ci95':bootstrap(rank),'mean_ev_gain_bb':statistics.fmean(ev)if ev else None,'ev_ci95':bootstrap(ev)}
if rows:
 n=sum(x['decisions']for x in rows);bad=sum(x['invalid_decisions']for x in rows);cp=aggregate_cleanup_protocol(rows);report['summary']={'mean_place':statistics.fmean(x['place']for x in rows),'mean_ev_bb':statistics.fmean(x['ev_bb']for x in rows),'decisions':n,'invalid':bad,'legal_rate':1-bad/n if n else None,'cleanup_protocol':cp,'cleanup_accepted_rate':cp['accepted_updated']/cp['turns']if cp['turns']else None,'talk_messages':sum(len(x['talk'])for x in rows)}
 if len(rows)==4:report['numeric_and_tools_gates_pass']=report['paired']['incumbent']['mean_rank_gain']>=.5 and report['paired']['rl20']['mean_rank_gain']>=-.5 and 1-bad/n>=.99 and cp['accepted_updated']/cp['turns']>=.98 and cp['wrong_tool_calls']==0
q=R/'summary.tmp';q.write_text(json.dumps(report,indent=2)+'\n');q.replace(R/'summary.json');print(json.dumps({k:v for k,v in report.items()if k not in['games','source_manifest']},indent=2))
