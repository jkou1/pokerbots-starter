"""Metadata-only fresh six-game FINAL reserve. Never deals cards or calls models."""
import json,hashlib,sys,collections,copy
from pathlib import Path
from datetime import datetime,timezone
from ac2.runtime import Task,Message,compute_content_hash
R=Path(__file__).resolve().parent;H=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training');E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments');M=R.parent/'cleanup-multihand-rl20-v1';sha=lambda b:hashlib.sha256(b).hexdigest()
if (R/'plan.json').exists():raise SystemExit('Frozen reserve exists; never regenerate after observing outcomes. Create a new version only with root authorization.')
def envseeds(file):
 seeds=[]
 if file.suffix=='.jsonl':
  for line in file.open():
   d=json.loads(line);v=d.get('env_params',{}).get('seed')
   if type(v)is int:seeds.append(v)
 else:
  d=json.loads(file.read_text());v=d.get('env_params',{}).get('seed')
  if type(v)is int:seeds.append(v)
 return seeds
current=H/'pokerbots-history-opponent-mixture-v2/pilot-train.jsonl';receipt=H/'pokerbots-history-opponent-mixture-v2/pilot-upload-verified.json';p=json.loads(receipt.read_text());assert p['actual_tasks']==7500 and p['exact_remote_prefix_hash_membership']and p['complete_for_pilot'];assert sha(current.read_bytes())==p['sha256'];cs=set(envseeds(current));assert len(cs)==7500 and len(p['task_ids'])==7500
late=E/'late-grpo-fresh64-v1/tasks.jsonl';ls=envseeds(late);lm=json.loads((E/'late-grpo-fresh64-v1/manifest.json').read_text());assert len(ls)==64 and set(ls)=={x['seed']for x in lm['task_metadata']};strata={}
for x in lm['task_metadata']:strata.setdefault(x['opponent_stratum'],set()).add(x['seed'])
original=H/'pokerbots-history-20k-v1/train.jsonl';priorfinal=E/'sealed-final-base20-v1/tasks.jsonl';oldself=H/'pokerbots-history-selfplay-ad74-v1/train.jsonl';pool=H/'pokerbots-history-opponent-mixture-v2/train.jsonl';joins={'current7500_vs_fixed_native64':len(cs&set(ls)),'by_native64_opponent_stratum':{k:{'seeds':len(v),'intersection':len(cs&v)}for k,v in strata.items()},'current7500_vs_original_historical20k':len(cs&set(envseeds(original))),'current7500_vs_old_selfplay20k':len(cs&set(envseeds(oldself))),'current7500_vs_prior_fullgame_final6':len(cs&set(envseeds(priorfinal))),'current7500_vs_retained_mixture_local20k_pool':len(cs&set(envseeds(pool))),'retained_pool_overlap_is_expected_subset_not_holdout_leak':True}
cells={}
for x in lm['task_metadata']:cells.setdefault(f"{x['opponent_stratum']}|seat{x['policy_seat']}",set()).add(x['seed'])
joins['by_native64_opponent_and_seat']={k:{'seeds':len(v),'intersection':len(cs&v)}for k,v in cells.items()}
prior={}
for directory in ['pokerbots-history-20k-v1','pokerbots-history-selfplay-ad74-v1']:
 for name in ['select','eval','smoke']:
  f=H/directory/f'{name}.jsonl'
  if f.exists():
   seeds=set(envseeds(f));prior[f'{directory}/{name}']={'seeds':len(seeds),'intersection':len(cs&seeds),'sha256':sha(f.read_bytes())}
joins['historical_select_eval_smoke_sets']=prior
assert all(x['intersection']==0 for x in prior.values())and all(x['intersection']==0 for x in joins['by_native64_opponent_and_seat'].values())
assert joins['current7500_vs_retained_mixture_local20k_pool']==7500
assert all(joins[k]==0 for k in ['current7500_vs_fixed_native64','current7500_vs_original_historical20k','current7500_vs_old_selfplay20k','current7500_vs_prior_fullgame_final6']);assert all(v['intersection']==0 for v in joins['by_native64_opponent_stratum'].values())
known=set();sources=[];files=set(E.glob('**/tasks.jsonl'))|set(E.glob('**/task.json'))
for directory in H.iterdir():
 if directory.is_dir()and directory.name.startswith('pokerbots-history-'):
  for name in ['train.jsonl','select.jsonl','eval.jsonl','smoke.jsonl','pilot-train.jsonl']:
   if(directory/name).exists():files.add(directory/name)
for f in M.glob('*-tasks.jsonl'):files.add(f)
for f in sorted(files):
 seeds=envseeds(f)
 if seeds:known.update(seeds);sources.append({'path':str(f),'task_seed_records':len(seeds),'unique_seeds':len(set(seeds)),'sha256':sha(f.read_bytes())})
ex=E/'selection-seed-exclusions.json';d=json.loads(ex.read_text());known.update(d['seeds']);sources.append({'path':str(ex),'seed_records':len(d['seeds']),'sha256':sha(ex.read_bytes())});mp=json.loads((M/'plan.json').read_text());memory={v for values in mp['fresh_seeds'].values()for v in values};known.update(memory)
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.collect_policy import deal_seeds
legacy=set()
for split in ['train','select','eval']:legacy.update(deal_seeds(split,1024))
known.update(legacy);sources.append({'source':'puredeal_seeds(train/select/eval,1024)from existingcollector; no cards generated','seed_records':len(legacy)})
seeds=[]
for seat in range(6):
 counter=0
 while True:
  seed=int(sha(f'fresh-final6-reserve-v2|2026-11-15|seat{seat}|{counter}'.encode())[:12],16)
  if seed not in known and seed not in seeds:seeds.append(seed);break
  counter+=1
# Existing published event contract; explicit supported rules, no model-specific hint.
tasks=[Task(input=[Message(role='user',content=f'Play an official six-seat30hand game from seat{seat}.')],env_params={'preset':'event','seed':seed,'seats':6,'total_hands':30,'starting_stack':200,'small_blind':1,'big_blind':2,'policy_seats':[seat],'submit_fields':['action','amount','say'],'opponent_model':'infer_21f395f49bff','opponent_timeout_seconds':120,'decision_timeout_seconds':300,'ev_labels':True,'ev_runouts':64},tags={'split':'final','purpose':'fresh-frozen-candidate-final-validation-only','source_group':f'fresh-final6-reserve-v2:{seed}','policy_seat':seat,'candidate_selection_must_precede_launch':True})for seat,seed in enumerate(seeds)];(R/'tasks.jsonl').write_text(''.join(x.model_dump_json()+'\n'for x in tasks));assert not(set(seeds)&known)
source=H/'catalog-base-standard-grpo-v1/effective-config.json';policy={'frozen_at':datetime.now(timezone.utc).isoformat(),'stage':'RESERVE ONLY; no uploads/evals/modelcalls','games':6,'policy_seats':list(range(6)),'seeds':seeds,'rules':{'seats':6,'initial_stacks':[200]*6,'small_blind':1,'big_blind':2,'hands':30,'carried_stacks':True,'rebuys':False,'hints':False},'fixed_opponent':{'inference_id':'infer_21f395f49bff','checkpoint':'ckpt_23b6b6239f26','expected_version':1,'all_five_opponent_seats':True},'reference':{'inference_id':'infer_b0f5e9429b7e','checkpoint':'ckpt_51eee61470f7','expected_version':1},'selected_candidate':None,'launch_requires_frozen_selection_decision':{'immutable_inference_checkpoint_version_before_any_game':True,'must_pass_fixed_native64_EV_protocol_gates':True,'root_GO_required':True,'same_tasks_rules_opponent_for_candidate_and_incumbent':True,'no_choice_or_retraining_from_these_final_outcomes':True},'tasks_sha256':sha((R/'tasks.jsonl').read_bytes()),'task_content_hashes':[compute_content_hash(x)for x in tasks],'known_distinct_seeds_excluded':len(known),'new_overlap_with_any_known':0,'memory_reserved_seeds_excluded':len(memory),'current7500_proof':{'path':str(current),'sha256':sha(current.read_bytes()),'remote_receipt':str(receipt),'receipt_sha256':sha(receipt.read_bytes()),'ordered_remote_task_ids':len(p['task_ids']),'current_effective_config_sha256':sha(source.read_bytes())},'seed_intersections':joins,'exclusion_sources':sources,'limitations':['Smalln6andwidepaireduncertainty.','Weakfixedbase20opponentpoolcannotguaranteeArena superiority.','Nativepolicysamplingdefaultsnotfullyexposed;pairedseedsarenotidenticalmodelresponses.','Paths/stacks/eliminationsmaydivergewithpolicyactions; no board/cardpeek or forcedfuturestate.'],'no_cards_or_boards_generated_or_inspected':True};(R/'plan.json').write_text(json.dumps(policy,indent=2)+'\n');(R/'seed-intersection-audit.json').write_text(json.dumps({'current7500_artifact_sha256':p['sha256'],'remote_receipt_sha256':sha(receipt.read_bytes()),'native64_task_sha256':sha(late.read_bytes()),'original20k_task_sha256':sha(original.read_bytes()),'prior_final_task_sha256':sha(priorfinal.read_bytes()),'intersections':joins,'no_models_or_cards':True},indent=2)+'\n');print(json.dumps({'six_seeds':seeds,'excluded':len(known),'intersections':joins,'task_sha256':policy['tasks_sha256']},indent=2))
