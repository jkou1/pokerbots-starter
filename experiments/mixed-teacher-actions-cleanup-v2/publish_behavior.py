import argparse,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
p=argparse.ArgumentParser();p.add_argument('--name',required=True);args=p.parse_args();R=Path(__file__).resolve().parent;file=R/f'{args.name}-behavior-summary.json';d=json.loads(file.read_text());m=d['mixed256'];pre=d['pre354'];clean=d['cleanup10'];hits=lambda action:round(m['per_action'][action]['recall']*m['per_action'][action]['examples'])
md=R/f'{args.name}-BEHAVIOR.md';md.write_text(f'''# LOCAL heldout behavior — {args.name}

Immutable inference `{d['inference_id']}`. These are teacher imitation, retention and functional protocol checks, not poker EV or a native Eval job. The same fixed256 records and exact source provenance were used as the preserved incumbent reference. No training, extension or promotion follows automatically.

| Frozen check | Observed | Required/reference |
|---|---:|---:|
| Mixed action agreement |{m['action_accuracy']:.2%}|incumbent75.78%|
| Mixed legal actions |{m['legal_rate']:.2%}|>=99%|
| Teacher bet recall |{hits('bet')}/27|>=7/27|
| Teacher check recall |{hits('check')}/43|>=39/43|
| Teacher fold recall |{hits('fold')}/118|incumbent110/118|
| Preflop agreement |{pre['action_accuracy']:.2%}|>=79.46%; incumbent84.46%|
| Preflop legal actions |{pre['legal_rate']:.2%}|>=99%|
| Strict cleanup protocol |{clean.get('valid')}/10|>=9/10|

Cleanup failure counts: {clean.get('missing_update_calls')} missing update calls, {clean.get('overlong')} overlong replies, {clean.get('wrong_tool_calls')} wrong-tool calls, {clean.get('unknown_argument_keys')} unknown-argument cases. Protocol validity does not establish factual memory quality. Enum regression: {d['enum4']['legal']}/4 legal.

Reported core gates pass: **{d['reported_core_gates_pass']}**. The JSON preserves negative findings and every group denominator, including teacher/street-balanced results. No checkpoint or source holdout was altered after observing these results. Expensive30hand evaluation is withheld while gates fail; no extension or promotion is justified by training-loss improvement alone. Remaining legacy postflop/factuality/workplace/official-poker gates are explicitly not claimed passed.

Raw private cleanup contents and regression inputs are excluded from these artifacts.
''')
c=working_client();identity=preflight_identity(c);slug='mixed-pete-carlos-actions-v1';coll=c.collections.get_by_slug(slug=slug);p=R/f'{args.name}-behavior-publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection_id':coll.id,'identity':identity,'local_not_native_eval':True,'artifacts':{}}
for source in [md,file]:
 if source.name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(source,collection=slug);receipt['artifacts'][source.name]={'id':a.id,'state':a.state,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()};p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
