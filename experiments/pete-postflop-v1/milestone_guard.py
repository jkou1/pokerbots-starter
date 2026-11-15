"""Reusable SFT milestone decision guard; never launches or extends a run.

A future coordinator supplies a predeclared policy and actual fixed-selection
receipt. --enforce-stop requires explicit per-run authorization and a recorded
checkpoint. Default is a read-only decision, suitable for a persistent poller.
"""
import argparse,json,math
from pathlib import Path

def assess(policy,observed):
 updates=observed['completed_updates'];milestones=policy['milestones']
 due=[m for m in milestones if updates>=m]
 if not due:return {'action':'continue','reason':'before first predeclared milestone'}
 milestone=max(due);validation=observed.get('validation')
 if not observed.get('checkpoint_id'):
  return {'action':'wait','reason':'preserve a recorded checkpoint before stopping','milestone':milestone}
 if not validation or validation.get('checkpoint_updates',-1)<milestone:
  action='stop' if updates>=policy['initial_max_updates'] else 'wait'
  return {'action':action,'reason':'no current fixed-selection evidence; no automatic extension','milestone':milestone}
 if any(not math.isfinite(validation[k]) for k in ['legal_rate','retention_rate','target_score','prior_target_score']):
  return {'action':'stop','reason':'invalid fixed-selection measurements','milestone':milestone}
 if validation['legal_rate']<policy['min_legal_rate'] or validation['retention_rate']<policy['min_retention_rate']:
  return {'action':'stop','reason':'fixed-selection reliability or retention regression','milestone':milestone}
 windows=observed.get('action_windows',[]);plateau=False
 if len(windows)>=2:
  a,b=windows[-2:]
  covered=all(v['samples']>=policy['min_samples_per_action'] for w in [a,b] for v in w['per_action'].values()) and set(a['per_action'])==set(b['per_action'])
  if covered and policy['focus_action'] in a['per_action']:
   relative=lambda old,new:(old-new)/max(abs(old),1e-12)
   macro_gain=relative(a['class_balanced_action_ce'],b['class_balanced_action_ce'])
   focus=policy['focus_action']
   focus_gain=relative(a['per_action'][focus]['action_ce'],b['per_action'][focus]['action_ce'])
   plateau=macro_gain<policy['min_relative_ce_gain'] and focus_gain<policy['min_relative_ce_gain']
 score_gain=validation['target_score']-validation['prior_target_score']
 if plateau and score_gain<policy['min_target_gain']:
  return {'action':'stop','reason':'action-specific plateau plus no fixed-selection target gain','milestone':milestone}
 if updates>=policy['initial_max_updates']:
  if validation['target_score']>=policy['extension_target_score'] and score_gain>=policy['min_target_gain'] and not plateau:
   return {'action':'eligible_for_extension','reason':'fixed-selection gain with continuing action learning','milestone':milestone,'extend_through':policy['next_max_updates']}
  return {'action':'stop','reason':'initial pilot cap reached without explicit extension evidence','milestone':milestone}
 return {'action':'continue','reason':'within initial cap; target/reliability evidence available','milestone':milestone}

def main():
 p=argparse.ArgumentParser();p.add_argument('--policy',type=Path,required=True);p.add_argument('--observed',type=Path,required=True);p.add_argument('--enforce-stop',action='store_true');args=p.parse_args()
 policy=json.loads(args.policy.read_text());observed=json.loads(args.observed.read_text());decision=assess(policy,observed);print(json.dumps(decision,indent=2))
 if args.enforce_stop and decision['action']=='stop':
  if not policy.get('automatic_stop_authorized') or not policy.get('train_id') or policy['train_id']!=observed.get('train_id'):raise SystemExit('Exact per-run automatic-stop authorization is required')
  from ac2.sdk import Client
  c=Client(project=policy.get('project','vals-hackathon'))
  if not any(x.id==observed['checkpoint_id'] for x in c.checkpoints.list(train_job_id=policy['train_id'])):raise SystemExit('Recorded checkpoint does not belong to this run')
  if not c.train.get(policy['train_id']).completed:c.train.stop(policy['train_id'])
if __name__=='__main__':main()
