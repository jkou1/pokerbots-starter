"""Label existing LOCAL baseline logs with the official EV helper; preserve raw files."""
import json,statistics,hashlib
from pathlib import Path
from collections import Counter
from poker_harness.ev import label_ev
from poker_harness.grading import seat_result
from vals_tools.game_score import game_rows,summarize_games
ROOT=Path(__file__).resolve().parent.parent/'data/experiments/overnight-incumbent-frozen-select';rows=[]
for f in sorted((ROOT/'logs').glob('*.json')):
 raw=f.read_bytes();log=json.loads(raw);seat=log['policy_seats'][0];label_ev(log,{seat},variants=8,runouts=64,redraw=False);(ROOT/'ev-labeled').mkdir(exist_ok=True);(ROOT/'ev-labeled'/f.name).write_text(json.dumps(log));result=seat_result(log,[seat]);cleanups=[h.get('cleanup',{}) for h in log['private'][seat]['hands'].values()];attempts=[a for c in cleanups for a in c.get('attempts',[])];rows.append({'seed':log['session_info']['seed'],'policy_seat':seat,'place':log['ranking']['places'][seat],'ev_bb':result.ev_bb,'realized_bb':result.realized_bb,'decisions':result.decisions,'invalid_decisions':result.format_errors,'cleanup_turns':len(cleanups),'cleanup_attempts':len(attempts),'cleanup_overlong_attempts':sum(len(a.get('contents') or '')>5000 for a in attempts),'cleanup_final_cut':sum(c.get('result')=='cut' for c in cleanups),'ev_methods':dict(Counter(h.get('ev',{}).get(seat,{}).get('method') for h in log['hands'])),'raw_source':str(f),'raw_sha256':hashlib.sha256(raw).hexdigest()})
r={'scope':'LOCAL official30hand baseline, not an AC2 native evaluation job. Exact raw logs preserved; EV labels computed afterward with unmodified official helper8variants64runouts/redrawFalse. Side-pot labels explicitly fall back to realized returns, not solverEV.','outcomes':summarize_games(game_rows(ROOT/'logs')),'mean_unclipped_ev_bb':statistics.fmean(x['ev_bb'] for x in rows),'games':rows,'cleanup_totals':{k:sum(x[k] for x in rows) for k in ['cleanup_turns','cleanup_attempts','cleanup_overlong_attempts','cleanup_final_cut']}};(ROOT/'summary.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='games'},indent=2))
