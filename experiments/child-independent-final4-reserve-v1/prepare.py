"""Root-authorized CPU-only independent child reserve; no deals, uploads or model calls."""
import json,hashlib,sys,copy
from pathlib import Path
from datetime import datetime,timezone
from ac2.runtime import Task,Message,compute_content_hash
R=Path(__file__).resolve().parent;F=R.parent/'fresh-final6-reserve-v2';H=Path('/Users/lance/Documents/pokerbots-starter-grpo-history/history/training');E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments');sha=lambda b:hashlib.sha256(b).hexdigest()
if(R/'plan.json').exists():raise SystemExit('Frozen reserve already exists; never regenerate after outcomes')
old=json.loads((F/'plan.json').read_text());known=set();sources=[]
def envseeds(path):
 records=[json.loads(l)for l in path.open()]if path.suffix=='.jsonl'else[json.loads(path.read_text())];return {x['env_params']['seed']for x in records if type(x.get('env_params',{}).get('seed'))is int}
for s in old['exclusion_sources']:
 if'path'not in s:continue
 p=Path(s['path']);assert sha(p.read_bytes())==s['sha256'],'Source mutation: retain freeze, investigate rather than silently revise'
 seeds=set(json.loads(p.read_text())['seeds'])if p.name=='selection-seed-exclusions.json'else envseeds(p);known|=seeds;sources.append({'path':str(p),'sha256':s['sha256'],'unique_seeds':len(seeds)})
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.collect_policy import deal_seeds
legacy=set().union(*(set(deal_seeds(split,1024))for split in ['train','select','eval']));known|=legacy
mp=json.loads((R.parent/'cleanup-multihand-rl20-v1/plan.json').read_text());memory={x for values in mp['fresh_seeds'].values()for x in values};known|=memory;assert len(known)==old['known_distinct_seeds_excluded']==44701
original44701=set(known);primary=set(old['seeds']);assert sha((F/'tasks.jsonl').read_bytes())==old['tasks_sha256'];known|=primary
current=H/'pokerbots-history-opponent-mixture-v2/pilot-train.jsonl';cs=envseeds(current);assert sha(current.read_bytes())==old['current7500_proof']['sha256']and len(cs)==7500;known|=cs
child=H/'base-grpo5-stability-v1/final-context-diversity.json';cd=json.loads(child.read_text());childseeds=set(cd['seeds']);assert len(childseeds)==cd['distinct_deal_seeds']==40 and childseeds<=cs;known|=childseeds
dev=E/'base20-development-v1/tasks.jsonl';ds=envseeds(dev);assert len(ds)==4;known|=ds
seats=[0,2,3,5];seeds=[]
for seat in seats:
 counter=0
 while True:
  seed=int(sha(f'child-independent-final4-reserve-v1|2026-11-15|seat{seat}|{counter}'.encode())[:12],16)
  if seed not in known and seed not in seeds:seeds.append(seed);break
  counter+=1
base=Task.model_validate_json((F/'tasks.jsonl').read_text().splitlines()[0]);tasks=[]
for seat,seed in zip(seats,seeds):
 env=copy.deepcopy(base.env_params);env.update(seed=seed,policy_seats=[seat]);tasks.append(Task(input=[Message(role='user',content=f'Play an official six-seat30hand game from seat{seat}.')],env_params=env,tags={'split':'final','purpose':'independent-child-validation-only-after-selection','source_group':f'child-independent-final4-reserve-v1:{seed}','policy_seat':seat,'child_selection_must_precede_launch':True,'never_use_parent_primary_FINAL6_to_select_child':True}))
(R/'tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n'for t in tasks));assert not(set(seeds)&known)
proof={'old_known44701_reconstructed':len(original44701),'total_distinct_excluded':len(known),'primary_FINAL6':{'seeds':len(primary),'intersection':len(set(seeds)&primary),'tasks_sha256':old['tasks_sha256']},'current7500':{'seeds':len(cs),'intersection':len(set(seeds)&cs),'sha256':sha(current.read_bytes())},'actual_child_contexts':{'seeds':len(childseeds),'intersection':len(set(seeds)&childseeds),'subset_of_current7500':True,'source_sha256':sha(child.read_bytes())},'dev4':{'seeds':len(ds),'intersection':len(set(seeds)&ds),'source_sha256':sha(dev.read_bytes())},'any_excluded_intersection':len(set(seeds)&known),'old_exclusion_plan_sha256':sha((F/'plan.json').read_bytes()),'source_hashes':sources,'no_cards_or_boards_generated_or_read':True};(R/'exclusion-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
plan={'frozen_at':datetime.now(timezone.utc).isoformat(),'stage':'CPU reserve only: no upload, modelcalls or automatic launch','games':4,'seats':seats,'seeds':seeds,'tasks_sha256':sha((R/'tasks.jsonl').read_bytes()),'content_hashes':[compute_content_hash(t)for t in tasks],'child_candidate':None,'child_source_run':'train_ed0649fc4923','candidate_checkpoint_version_selection_must_be_frozen_before_launch':True,'baseline_parent5':{'checkpoint':'ckpt_a7a227300baf','inference_id':'infer_af5fa217b570','version':1},'optional_C_arm_only_if_root_GO':{'checkpoint':'ckpt_51eee61470f7','inference_id':'infer_b0f5e9429b7e','version':1},'same_fixed_base20_opponents':old['fixed_opponent'],'rules':old['rules'],'root_GO_for_upload_and_launch_still_required':True,'launch_condition':'Child first passes frozen native64 versus parent5: pairedgain>=0.5BB,bothstrata>=0,legal>=99%,64exactcleanup; sufficienttime and separate rootGO.','primary_parent_FINAL6_never_used_to_choose_child':True,'no_alternative_child_on_same_final_after_outcomes':True,'exclusion_proof_sha256':sha((R/'exclusion-proof.json').read_bytes()),'limitations':['Smalln4,wideuncertainty.','Fixedweakbase20opponentpool and non-Arena policy samplinglimittransfer.','Pairedseeds do not force identical trajectories after decisions.'],'no_child_generated_selection_outputs_or_primary_FINAL_outcomes_read':True,'no_cards_or_boards_generated_or_inspected':True};(R/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({k:plan[k]for k in ['frozen_at','games','seats','seeds','tasks_sha256','exclusion_proof_sha256']},indent=2))
