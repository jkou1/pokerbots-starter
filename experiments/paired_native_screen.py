"""Paired fixed-task checkpoint screening from native unclipped grader artifacts."""
import argparse,json,os,statistics
from pathlib import Path
from ac2.sdk import Client
from vals_tools.game_score import bootstrap
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--parent',default='eval_7353b52d4873');p.add_argument('--label',required=True);a=p.parse_args();c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);out=Path(__file__).resolve().parent.parent/'data/experiments/rl-checkpoint-selection'/a.label;out.mkdir(parents=True,exist_ok=True)
def read(rid):
 run=c.eval.get(rid);scores=c.analytics.scores(run_ids=[rid]).to_records();grade=c.analytics.spans(run_ids=[rid]).select('output','attributes').filter(name='grade').to_records();artifacts={}
 for x in grade:
  try:artifacts[json.loads(x['attributes'])['agent_trace_id']]=json.loads(x['output']).get('artifacts',{})
  except (ValueError,KeyError,TypeError):continue
 rows={}
 for x in scores:
  art=artifacts.get(x['agent_trace_id'],{});rows[x['datapoint_id']]={'reward':x['score'],'ev_bb':art.get('ev_bb'),'realized_bb':art.get('realized_bb'),'decisions':art.get('policy_decisions'),'format_errors':art.get('policy_format_errors'),'method':art.get('ev_method'),'reasoning':x['reasoning'],'full_artifacts':art}
 return {'eval_id':rid,'status':run.status,'tasks':rows}
parent_cache=out.parent/'parent32-artifacts.json'
if parent_cache.exists():
 parent=json.loads(parent_cache.read_text());assert parent['eval_id']==a.parent
else:
 parent=read(a.parent)
 if parent['status']=='succeeded' and len(parent['tasks'])==32:parent_cache.write_text(json.dumps(parent,indent=2))
candidate=read(a.candidate);common=set(parent['tasks'])&set(candidate['tasks']);paired=[]
for key in sorted(common):
 if parent['tasks'][key]['ev_bb'] is not None and candidate['tasks'][key]['ev_bb'] is not None:paired.append(candidate['tasks'][key]['ev_bb']-parent['tasks'][key]['ev_bb'])
def metrics(run):
 rows=list(run['tasks'].values());ev=[x['ev_bb'] for x in rows if x['ev_bb'] is not None];decisions=sum(x['decisions'] or 0 for x in rows);errors=sum(x['format_errors'] or 0 for x in rows)
 return {'eval_id':run['eval_id'],'status':run['status'],'graded_tasks':len(rows),'unclipped_ev_coverage':len(ev),'mean_unclipped_ev_bb':statistics.fmean(ev) if ev else None,'policy_decisions':decisions,'invalid_decisions':errors,'invalid_rate':errors/decisions if decisions else None,'technical_failure_without_ev':sum(x['ev_bb'] is None for x in rows),'mean_clipped_reward':statistics.fmean(x['reward'] for x in rows) if rows else None}
r={'candidate':metrics(candidate),'parent':metrics(parent),'paired_tasks':len(paired),'candidate_minus_parent_ev_bb':statistics.fmean(paired) if paired else None,'paired_bootstrap_ci95':bootstrap(paired) if paired else [None,None],'scope':'Fixed-deal/seat/opponent single-hand selection screen; not official30hand placement or Arena rating. EV artifact can fall back to realized for unsupported side pots. Clipped reward is diagnostic only, never convergence proof.','candidate_tasks':candidate['tasks'],'parent_tasks':parent['tasks']};(out/'summary.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['candidate_tasks','parent_tasks']},indent=2))
