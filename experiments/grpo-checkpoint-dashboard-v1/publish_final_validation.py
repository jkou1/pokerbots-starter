"""Publish final validation of ONE previously frozen candidate, never ranking."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;S=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/sealed-final-base20-v1');read=lambda n:json.loads((S/n).read_text())
choice=read('selection-decision.json');summary=read('summary.json');recommend=read('promotion-recommendation.json');workplace=read('workplace-final-review.json')
assert choice['inference_id']=='infer_9efa1c614a32' and summary['matched_games']==6
assert choice['selected_at']<summary['runs']['candidate']['submitted_at']
assert workplace['elapsed_from_recorded_start_seconds']<=workplace['time_budget_seconds']==300
for run in summary['runs'].values():assert run['status']=='succeeded' and run['completed_games']==run['planned_games']==6
clean={**summary,'runs':{name:{k:v for k,v in run.items() if k not in ['games','source_manifest']} for name,run in summary['runs'].items()},'evidence_stage':'FINAL VALIDATION, not selection/checkpoint ranking','no_training_reuse':True,'one_frozen_candidate':True}
(R/'FINAL_VALIDATION_SUMMARY.json').write_text(json.dumps(clean,indent=2)+'\n')
receipt={'stage':'FINAL VALIDATION for one selected/frozen candidate','selected_at':choice['selected_at'],'candidate_final_submitted_at':summary['runs']['candidate']['submitted_at'],'selected_before_final_submission':True,'inference_id':choice['inference_id'],'checkpoint':choice['checkpoint'],'version':choice['version'],'decision':choice['decision'],'frozen_policy':choice['frozen_policy'],'source_sha256':{name:hashlib.sha256((S/name).read_bytes()).hexdigest() for name in ['selection-decision.json','summary.json','promotion-recommendation.json','workplace-final-review.json']},'no_training_reuse':True,'recommendation':recommend['decision'],'actual_arena_promotion':False,'canary_active':False,'operational_blocker':recommend['gate_assessment']['operational_arena_control'],'workplace_review':workplace,'limitations':recommend['limitations']}
(R/'FINAL_VALIDATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'FINAL_VALIDATION_README.md').write_text('''# FINAL VALIDATION — one candidate frozen before final submission

RL20 was selected and version-pinned before its final job was submitted. This six-game final set was used for this one frozen candidate, not checkpoint ranking; no training reuse is permitted. Its final evidence is now consumed. Future candidate comparisons need a fresh final release.

| Final six matched games | Incumbent | Frozen RL20 |
|---|---:|---:|
| Mean placement (lower is better) |3.1667|2.0000|
| Mean unclipped EV (BB/game) |16.0103|91.3765|
| Invalid policy decisions |0/309|2/298|
| Busts |0/6|0/6|
| Exact accepted cleanup updates |139/180|180/180|
| Final cleanup cuts |41|0|

Paired placement improvement+1.1667,95%bootstrapCI[-0.6667,+2.6667]. Paired unclipped EV gain+75.3662BB/game,CI[-23.208,+170.3355]. Both intervals include zero. This is directional evidence with substantial uncertainty, not proven Arena superiority. Clipped dashboard reward is a different signal. EV uses the official adjustment, with unsupported sidepots falling back to realized returns.

RL20 had two genuine enum errors (0.671%); both exact error states were legal in all8repeat probes. Clean repeats do not erase the observed failures. Betting passivity persists in teacher imitation. Cleanup protocol validity does not imply factual memory quality. Bounded workplace review took111.11seconds of a300second budget: all298final decisions were silent; absence of inappropriate emitted talk in observed coverage is not a future guarantee.

Recommendation: eligible for a monitored canary only when actual authenticated promotion and rollback control exist. No Arena promotion occurred and the canary remains inactive. The incumbent rollback deployment is preserved. The companion receipt records frozen-choice timing, source hashes and remaining limitations without uploading raw private traces.
''')
c=working_client();identity=preflight_identity(c);slug='grpo-checkpoint-decisions-20261115';coll=c.collections.get_by_slug(slug=slug)
ids=['eval_be4a7c44dc07','eval_8a14524c0e64']
for ident in ids:
 d=c._require_api().request('GET',f'/eval/{ident}').json();assert d['status']=='succeeded' and d['project_id']=='prj_ba36d29befaf'
preflight_identity(c);c.collections.add_eval_runs(collection_id=coll.id,ids=ids)
p=R/'final-validation-publication.json';published=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'identity':identity,'stage':'FINAL VALIDATION, not selection','native_eval_ids':ids,'artifacts':{}}
for name in ['FINAL_VALIDATION_README.md','FINAL_VALIDATION_SUMMARY.json','FINAL_VALIDATION_RECEIPT.json']:
 if name in published['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);published['artifacts'][name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(published,indent=2)+'\n')
print(json.dumps(published,indent=2))
