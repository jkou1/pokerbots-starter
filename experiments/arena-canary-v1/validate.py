"""Recorded-only parser validation; no model or API calls, no training data."""
import json,hashlib,collections
from pathlib import Path
from parser import analyze,decoded,parse_legal
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments')
p=E/'arena-schema-inspection/actual-arena-input-output.json';actual=json.loads(p.read_text());actual=actual.get('rows',[]) if isinstance(actual,dict) else actual
parsed=[analyze(r) for r in actual];assert len(parsed)==12 and all(x is not None for x in parsed)
assert all(r['kind'] in ['decision','cleanup'] for r in parsed)
q=E/'native-official30/base-s20/enum-invalid-exact-inputs.json';cases=json.loads(q.read_text())['cases'];native=[]
for case in cases:
 row={'input':case['input'],'output':case['output'],'trace_id':case['trace_id'],'start_time':case['time'],'attributes':{}}
 native.append(analyze(row,require_arena=False))
assert sum('invalid_action_enum' in r['errors'] for r in native)>=2
assert sum('wrong_tool' in r['errors'] for r in native if r['kind']=='cleanup')>=1
assert analyze({'attributes':{'conversation_id':'native/not-arena'},'input':'[]','output':'[]'}) is None
p95=E/'native-official30/base-s20/enum-native-spans.json';spans=json.loads(p95.read_text());allnative=[analyze(r,require_arena=False) for r in spans]
assert parse_legal('Legal actions: fold, call 2, raise to 6-224')=={'fold':True,'call':2,'raise':[6,224]}
assert parse_legal('Legal actions: check, bet to 2-220')=={'check':True,'bet':[2,220]}
# Exercise visible total bounds/check availability with recorded observations and a
# deliberately modified output fixture. These are parser tests, never teacher targets.
base=next(r for r in actual if 'raise to' in str(r['input']));bad=dict(base);bad['output']=json.dumps([{'type':'function_call','name':'submit_action','arguments':json.dumps({'action':'check'})}]);assert 'action_not_legal' in analyze(bad)['errors']
visible=decoded(base['input']);text=[x['content'] for x in visible if x.get('role')=='user'][-1];lo,hi=parse_legal(text)['raise'];bad['output']=json.dumps([{'type':'function_call','name':'submit_action','arguments':json.dumps({'action':'raise','amount':hi+1})}]);assert 'amount_outside_visible_street_total_bounds' in analyze(bad)['errors']
report={'actual_arena_fixtures':len(parsed),'arena_kinds':dict(collections.Counter(r['kind'] for r in parsed)),'arena_detected_errors':dict(collections.Counter(e for r in parsed for e in r['errors'])),'native_exact_cases':len(native),'known_native_detected_errors':dict(collections.Counter(e for r in native for e in r['errors'])),'native_control_and_failure_spans':len(allnative),'native95_detected_errors':dict(collections.Counter(e for r in allnative for e in r['errors'])),'non_arena_excluded':True,'visible_raise_total_and_check_fixture_tests_passed':True,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [p,q,p95]},'no_model_calls':True,'no_training_use':True,'private_evidence_not_copied_to_git':True}
(R/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
