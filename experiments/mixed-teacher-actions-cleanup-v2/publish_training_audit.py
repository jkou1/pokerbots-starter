"""Publish aggregate managed pilot evidence; no private token traces or fake evals."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;ce=json.loads((R/'pilot10-action-ce.json').read_text());assert ce['training_updates']==10 and ce['managed_steps']==10 and ce['all_full_batches'] and ce['all_target_audits_passed']
a=json.loads((R/'managed-aggregate-audit.json').read_text());assert len(a['actual_managed_steps'])==10
(R/'pilot10-managed-target-audit.json').write_text(json.dumps(a,indent=2)+'\n')
(R/'PILOT10_AUDIT_README.md').write_text('''# Completed10-update pilot: actual managed target audit

The approved pilot reached10updates without extension. All1,280 actual managed sequences(10full128-example batches) passed source membership, nonempty reasoning scaffold, explicitly supervised reasoning close, exactly one correct tool call and no teacher identity in student prompts.

Actual sampled participation:620Pete actions,651Carlos actions,9genuine cleanup controls. Three of the four validated cleanup sources were sampled during this short pilot; all four remain in the full dataset. Actual cleanup target tokens were3.36%of supervised tokens, versus4.63%in the full dataset. Backend sampling differs from source order; both are documented rather than conflated.

| Actual argument CE, changing minibatches | Updates0–4 | Updates5–9 |
|---|---:|---:|
| Class-balanced action CE |0.9529|0.9254|
| Bet argument CE |1.0979|0.9473|
| Raise argument CE |1.2345|0.9449|
| Amount-digit CE |1.9556|1.5115|

The macro decrease is approximately2.9%; check/fold CE rose across different minibatches. This is modest continuing training signal, not fixed validation, convergence, or poker EV. The first checkpoint and final checkpoint were registered; serving conversion and fixed256/cleanup/retention evidence are required next. No extension or promotion is authorized by training loss alone.

Startup was initially quiet, but actual allocation, target loading, forward traces and finite optimizer updates established progress. It resolved without a restart. The startup brief preserves the bounded five-minute no-progress diagnostic rule without claiming continuous GPU activity. Private exact token traces and scratchpad contents are not uploaded here.
''')
c=working_client();identity=preflight_identity(c);slug='mixed-pete-carlos-actions-v1';coll=c.collections.get_by_slug(slug=slug);p=R/'pilot10-audit-publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'identity':identity,'local_evaluations_fabricated':False,'artifacts':{}}
for name in ['PILOT10_AUDIT_README.md','pilot10-action-ce.json','pilot10-managed-target-audit.json','early-offline-audit.json','startup-triage-brief.json','remote-list-order-audit.json','local-template-length-audit.json']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);art=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':art.id,'state':art.state,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
