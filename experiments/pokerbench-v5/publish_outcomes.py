"""Publish only aggregate frozen outcomes; no private traces or fabricated eval records."""
import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/late-grpo-fresh64-v1');c=working_client();identity=preflight_identity(c);slug='pokerbench-v5-reconciled-knowledge-pilot';coll=c.collections.get_by_slug(slug=slug)
local={'kind':'LOCAL frozen imitation/protocol diagnostics, not nativeEval or pokerEV','knowledge_gate_pass':False,'no_extension':True}
for tag in ['s10','s20']:
 p=R/f'candidate-{tag}';local[tag]={n:json.loads((p/f'{n}.json').read_text())for n in ['pokerbench-select136-summary','original41-subset-summary','preflop-select354-summary','cleanup-stress10-summary','complete']}
(R/'LOCAL_CANDIDATE_OUTCOMES.json').write_text(json.dumps(local,indent=2)+'\n')
allsummary=json.loads((E/'summary.json').read_text());native={'kind':'Actual native64 outcome, prospective final20-only EV screen; knowledge failed independently','native_eval_id':'eval_284f73e12461','run':allsummary['runs']['v5-final20'],'paired_both':json.loads((E/'v5-final20-vs-both.json').read_text()),'frozen_interpretation':json.loads((E/'v5-frozen-gate-interpretation.json').read_text()),'invalid_aggregate':json.loads((E/'v5-final20-invalid-audit.json').read_text()),'conclusion':'No advancement. Positive noisy aggregate versus20 does not pass the predeclared both-opponent-strata gate. No SFT extension or teacher-quality claim.'}
# The invalid audit is inspected separately below before publication: only aggregate/nonprivate fields are retained.
audit=native.pop('invalid_aggregate');native['invalid_audit_source_sha256']=hashlib.sha256((E/'v5-final20-invalid-audit.json').read_bytes()).hexdigest();native['invalid_aggregate']={'count':len(audit),'errors':[x['model_response']['error']for x in audit],'source_harness_fallback_applied':sum(bool(x['model_response'].get('fallback_used'))for x in audit),'distinction':'No inference-provider fallback; both invalid host actions applied safe fold. Actual112/114 decisions legal.'}
(R/'NATIVE_FINAL20_EV_SCREEN.json').write_text(json.dumps(native,indent=2)+'\n')
p=R/'outcome-publication.json';receipt=json.loads(p.read_text())if p.exists()else{'collection_id':coll.id,'identity':identity,'artifacts':{}}
for name in ['LOCAL_CANDIDATE_OUTCOMES.json','NATIVE_FINAL20_EV_SCREEN.json']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest(),'state':a.state};p.write_text(json.dumps(receipt,indent=2)+'\n');print(name,a.id)
if not receipt.get('native_eval_linked'):
 preflight_identity(c);c.collections.add_eval_runs(collection_id=coll.id,ids=['eval_284f73e12461']);receipt['native_eval_linked']=True;p.write_text(json.dumps(receipt,indent=2)+'\n')
print(coll.id)
