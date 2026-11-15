"""Read only development eval outcomes; never open sealed final outcomes."""
import hashlib,json,os,statistics
from collections import Counter
from pathlib import Path
from ac2.sdk import Client
from poker_harness.grading import seat_result
from vals_tools.game_score import bootstrap
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/base20-development-v1'
SOURCE=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs')
r=json.loads((ROOT/'receipt.json').read_text());seats={seed:'seat'+str(i) for i,seed in enumerate(r['seeds'])};c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);result={'scope':'Selection-only four paired official30hand development games. Raw EV uses official harness adjustment, with unsupported sidepots falling back to realized returns. Small sample, no claim of convergence.','frozen_opponent':r['frozen_opponent'],'runs':{}}
for label,meta in r['runs'].items():
 run=c.eval.get(meta['eval_id']);out=ROOT/label;out.mkdir(exist_ok=True);rows=[];manifest=[]
 for path in SOURCE.glob('*.json'):
  try:raw=path.read_bytes();log=json.loads(raw)
  except (OSError,json.JSONDecodeError):continue
  if log.get('relay_job_id')!=run.job_id or not log.get('complete'):continue
  seed=log['session_info']['seed'];assert seed in seats;seat=seats[seed];graded=seat_result(log,[seat]);cleanups=[h.get('cleanup',{}) for h in log.get('private',{}).get(seat,{}).get('hands',{}).values()];attempts=[a for cleanup in cleanups for a in cleanup.get('attempts',[])]
  talk=[{'say':a['model_response'].get('say'),'raw':a['model_response'].get('private',{}).get('say_raw')} for h in log['hands'] for a in h['actions'] if a['player']==seat and (a['model_response'].get('say') or a['model_response'].get('private',{}).get('say_raw'))]
  row={'seed':seed,'seat':seat,'place':log['ranking']['places'][seat],'busted':seat in log.get('eliminated_on_hand',{}),'ev_bb':graded.ev_bb,'realized_bb':graded.realized_bb,'decisions':graded.decisions,'invalid_decisions':graded.format_errors,'hands':graded.hands,'cleanup_turns':len(cleanups),'cleanup_attempts':len(attempts),'cleanup_overlong_attempts':sum(len(a.get('contents') or '')>5000 for a in attempts),'cleanup_final_cut':sum(x.get('result')=='cut' for x in cleanups),'ev_methods':dict(Counter(h.get('ev',{}).get(seat,{}).get('method') for h in log['hands'])),'talk':talk};rows.append(row)
  (out/'raw').mkdir(exist_ok=True);(out/'raw'/path.name).write_bytes(raw);manifest.append({'source':str(path),'raw_sha256':hashlib.sha256(raw).hexdigest(),'seed':seed,'relay_job_id':run.job_id})
 rows.sort(key=lambda x:x['seed']);assert len({x['seed'] for x in rows})==len(rows)
 record=meta|{'job_id':run.job_id,'status':run.status,'completed_games':len(rows),'planned_games':4,'games':rows,'source_manifest':manifest}
 if rows:
  record['summary']={**{key:statistics.fmean(x[key] for x in rows) for key in ['place','ev_bb','realized_bb','busted']},**{key:sum(x[key] for x in rows) for key in ['decisions','invalid_decisions','cleanup_turns','cleanup_attempts','cleanup_overlong_attempts','cleanup_final_cut']}}
 result['runs'][label]=record
if all(label in result['runs'] for label in ['incumbent','rl20']):
 base={x['seed']:x for x in result['runs']['incumbent']['games']};new={x['seed']:x for x in result['runs']['rl20']['games']};common=sorted(base.keys()&new.keys());result['matched_games']=len(common)
 if common:
  result['paired']={}
  for metric,diffs in {'ev_gain_bb':[new[s]['ev_bb']-base[s]['ev_bb'] for s in common],'placement_improvement':[base[s]['place']-new[s]['place'] for s in common],'realized_gain_bb':[new[s]['realized_bb']-base[s]['realized_bb'] for s in common]}.items():result['paired'][metric]={'mean':statistics.fmean(diffs),'ci95':bootstrap(diffs),'individual_differences':diffs}
(ROOT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'matched_games':result.get('matched_games'),'paired':result.get('paired'),'runs':{k:{x:v[x] for x in ['eval_id','status','completed_games'] }|{'summary':v.get('summary')} for k,v in result['runs'].items()}},indent=2))
