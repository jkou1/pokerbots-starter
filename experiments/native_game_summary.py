"""Summarize native eval's raw attributed games, not its clipped reward."""
import argparse,json,os,hashlib,statistics
from collections import Counter
from pathlib import Path
from ac2.sdk import Client
from poker_harness.grading import seat_result
from vals_tools.cleanup_score import cleanup_protocol,aggregate_cleanup_protocol
from vals_tools.collect_policy import deal_seeds
from vals_tools.game_score import game_rows,summarize_games,bootstrap
ROOT=Path(__file__).resolve().parent.parent/'data/experiments'
SOURCE=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs')
p=argparse.ArgumentParser();p.add_argument('--eval',required=True);p.add_argument('--label',required=True);a=p.parse_args();c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);run=c.eval.get(a.eval);out=ROOT/'native-official30'/a.label;out.mkdir(parents=True,exist_ok=True);seeds=deal_seeds('select',6);seats={s:i for i,s in enumerate(seeds)};manifest=[];rows=[]
for f in SOURCE.glob('*.json'):
 try:
  raw=f.read_bytes();log=json.loads(raw)
  if log.get('relay_job_id')!=run.job_id or not log.get('complete'):continue
  seed=log['session_info']['seed']
  if seed not in seats:raise ValueError('Native job produced unknown game seed')
  seat='seat'+str(seats[seed]);(out/'raw').mkdir(exist_ok=True);(out/'raw'/f.name).write_bytes(raw);log.update(policy_seats=[seat],opponent_model='vals-hackathon/selfplay-ad74c826c9ad',split='select');(out/'logs').mkdir(exist_ok=True);(out/'logs'/f'{seed}.json').write_text(json.dumps(log));result=seat_result(log,[seat]);cleanups=[h.get('cleanup',{}) for h in log.get('private',{}).get(seat,{}).get('hands',{}).values()];attempts=[attempt for cleanup in cleanups for attempt in cleanup.get('attempts',[])];talk=[{'say':act['model_response'].get('say'),'raw':act['model_response'].get('private',{}).get('say_raw')} for hand in log['hands'] for act in hand['actions'] if act['player']==seat and (act['model_response'].get('say') or act['model_response'].get('private',{}).get('say_raw'))]
  rows.append({'seed':seed,'policy_seat':seat,'place':log['ranking']['places'][seat],'ev_bb':result.ev_bb,'realized_bb':result.realized_bb,'decisions':result.decisions,'invalid_decisions':result.format_errors,'hands':result.hands,'ev_methods':dict(Counter(h.get('ev',{}).get(seat,{}).get('method') for h in log['hands'])),'cleanup_protocol':cleanup_protocol(cleanups),'cleanup_turns':len(cleanups),'cleanup_attempts':len(attempts),'cleanup_overlong_attempts':sum(len(x.get('contents') or '')>5000 for x in attempts),'cleanup_final_cut':sum(x.get('result')=='cut' for x in cleanups),'talk':talk});manifest.append({'source':str(f),'raw_sha256':hashlib.sha256(raw).hexdigest(),'seed':seed,'source_relay_job_id':run.job_id})
 except (json.JSONDecodeError,OSError):continue
summary={'eval_id':a.eval,'job_id':run.job_id,'status':run.status,'planned_games':6,'completed_logs':len(rows),'scope':'Actual native official30hand games; unclipped EV and raw placement. Dashboard primary reward is clipped and is not a placement metric. EV is the official harness adjustment; unsupported side pots fall back to realized returns, not solver EV.','games':rows,'source_manifest':manifest}
if rows:
 native=game_rows(out/'logs');parent=game_rows(ROOT/'overnight-incumbent-frozen-select/logs');common=native.keys()&parent.keys();summary['outcomes']=summarize_games(native);summary['mean_unclipped_ev_bb']=statistics.fmean(x['ev_bb'] for x in rows)
 if common:summary['paired_vs_incumbent']=summarize_games({k:native[k] for k in sorted(common)},{k:parent[k] for k in sorted(common)})
 baseline_path=ROOT/'overnight-incumbent-frozen-select/summary.json'
 if baseline_path.exists():
  baseline={row['seed']:row for row in json.loads(baseline_path.read_text())['games']};diffs=[row['ev_bb']-baseline[row['seed']]['ev_bb'] for row in rows if row['seed'] in baseline];summary['paired_unclipped_ev_vs_incumbent']={'games':len(diffs),'mean_difference_bb':statistics.fmean(diffs) if diffs else None,'bootstrap_ci95':bootstrap(diffs),'baseline_EV_scope':'Official helper applied after local baseline games with same8variants/64runouts; raw logs unchanged.'}
 summary['cleanup_protocol']=aggregate_cleanup_protocol(rows)
 summary['cleanup_totals']={key:sum(x[key] for x in rows) for key in ['cleanup_turns','cleanup_attempts','cleanup_overlong_attempts','cleanup_final_cut']}
summary['native_scores']=c.analytics.scores(run_ids=[a.eval]).to_records();(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['games','source_manifest','native_scores']},indent=2))
