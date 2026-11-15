"""Root-authorized exact frozen6 upload only; never launches models or changes seeds."""
import json,hashlib,sys,time
from pathlib import Path
from ac2.runtime import Task,compute_content_hash
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;sha=lambda x:hashlib.sha256(x).hexdigest();plan=json.loads((R/'plan.json').read_text());assert sha((R/'tasks.jsonl').read_bytes())==plan['tasks_sha256']=='d3bf239d555adba594481780bc57501aa2ce1f12d0834dac726bf63a4713bfdf';tasks=[Task.model_validate_json(l)for l in(R/'tasks.jsonl').open()];expected={compute_content_hash(t):t for t in tasks};assert list(expected)==plan['task_content_hashes']and len(expected)==6;assert [t.env_params['seed']for t in tasks]==plan['seeds']and[t.env_params['policy_seats'][0]for t in tasks]==list(range(6))
c=working_client();identity=preflight_identity(c);pins={'candidate':('infer_af5fa217b570','ckpt_a7a227300baf'),'incumbent':('infer_b0f5e9429b7e','ckpt_51eee61470f7'),'opponent':('infer_21f395f49bff','ckpt_23b6b6239f26')};verified={}
for k,(infer,ckpt)in pins.items():
 v=c.inference.get(infer);assert v.checkpoint_id==ckpt and v.version==1;verified[k]={'inference_id':infer,'checkpoint':ckpt,'version':v.version,'state':v.state}
dev=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/base-grpo5-development-v1/summary.json');d=json.loads(dev.read_text());assert d['completed_games']==4 and d['numeric_and_tools_gates_pass']is True
freeze=R/'selection-freeze.json'
if not freeze.exists():freeze.write_text(json.dumps({'frozen_epoch':time.time(),'root_FINAL6_GO':True,'selected_candidate_only':verified['candidate'],'reference':verified['incumbent'],'fixed_opponent':verified['opponent'],'development_eval_id':'eval_c86991deffcc','development_summary_sha256':sha(dev.read_bytes()),'development_practical_gate_pass':True,'workplace_review':'Root/evalowner completed and passed before FINALGO; no broad factual-memory pass implied.','known_factual_memory_errors_preserved':'Initial8milestone review:5blind-positionerrors,1own-card-suiterror; currentboard/stacksconsistent where stated. No factual improvement claim.','independent_child_may_not_replace_parent_on_these_FINAL_results':True,'no_checkpoint_choice_retraining_or_extra_variant_from_final':True,'tasks_sha256':plan['tasks_sha256'],'exclusion_plan_sha256':sha((R/'plan.json').read_bytes()),'exclusion_proof_sha256':sha((R/'seed-intersection-audit.json').read_bytes()),'seeds_frozen_before_candidate_selection':True,'new_seeds_or_cards_generated':False,'no_model_calls_by_data_agent':True},indent=2)+'\n')
else:assert json.loads(freeze.read_text())['selected_candidate_only']['inference_id']==pins['candidate'][0]
name='pokerbots-fresh-final6-reserve-v2';p=R/'upload-receipt.json';receipt=json.loads(p.read_text())if p.exists()else{'dataset_name':name,'identity':identity,'file_sha256':plan['tasks_sha256'],'selection_freeze_sha256':sha(freeze.read_bytes()),'expected':6,'status':'preparing'};save=lambda:p.write_text(json.dumps(receipt,indent=2)+'\n');save()
preflight_identity(c);ds=c.datasets.create(name,description='Exactly6frozenFINALvalidationgames,seats0–5,selectedparentGRPO5vsactualC,notcheckpointselection.No newseedsorboards.',exist_ok=True);receipt['dataset_id']=ds.id;save()
def members():
 refs=c.datasets.list_tasks(name,offset=0,limit=100);assert len(refs)<=6;return {x.content_hash:x.id for x in refs}
actual=members();assert set(actual)<=set(expected),'Unexpected tasks; refuse mutation'
missing=[t for h,t in expected.items()if h not in actual]
if missing:receipt['status']='upload_requested';save();preflight_identity(c);receipt['returned_new_task_ids']=c.datasets.add_tasks(name,tasks=missing);save()
actual=members();assert set(actual)==set(expected)and len(actual)==6
checks=[]
for h,t in expected.items():
 loaded=c.datasets.load_task(actual[h]);assert loaded.content_hash==h;assert loaded.model_dump(exclude={'id','content_hash'},mode='json')==t.model_dump(exclude={'id','content_hash'},mode='json');checks.append({'task_id':actual[h],'content_hash':h,'exact_input_env_tags_name_description_grader_verified':True})
receipt.update(status='verified',task_ids=[actual[h]for h in expected],content_hashes=list(expected),all6_full_payload_verified=True,exact_membership=True,stable_membership_recheck=members()==actual,checks=checks,verified_epoch=time.time(),no_model_calls=True);save();print(json.dumps(receipt,indent=2),flush=True)
