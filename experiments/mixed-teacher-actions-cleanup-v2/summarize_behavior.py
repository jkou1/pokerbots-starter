"""Aggregate only LOCAL heldout checks; exact private cleanup texts excluded."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval')
from vals_tools.pete_eval import imitation_metrics
p=argparse.ArgumentParser();p.add_argument('--name',required=True);args=p.parse_args()
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments');S=R.parent/'mixed-teacher-actions-v1/fast-select.jsonl';rows=[json.loads(l) for l in S.open()]
rawpath=E/'mixed-teacher-select'/f'{args.name}.json';d=json.loads(rawpath.read_text());assert d['status']=='complete' and len(d['results'])==len(rows)==256
assert all(x['provenance']==y['provenance'] for x,y in zip(rows,d['results']))
groups=collections.defaultdict(list)
for i,row in enumerate(rows):
 for kind,key in [('teacher',row['provenance']['teacher']),('street',row['provenance']['street']),('teacher_street',row['provenance']['teacher']+':'+row['provenance']['street'])]:groups[(kind,key)].append(i)
summary={'scope':'LOCAL heldout imitation/retention/protocol checks, not native Eval or poker EV','name':args.name,'inference_id':d['model'],'mixed256':d['summary'],'source_hashes':{str(rawpath):hashlib.sha256(rawpath.read_bytes()).hexdigest(),str(S):hashlib.sha256(S.read_bytes()).hexdigest()},'stratified':{}}
for (kind,key),indices in groups.items():summary['stratified'].setdefault(kind,{})[key]=imitation_metrics([rows[i] for i in indices],[d['results'][i]['action'] for i in indices])
for kind in ['teacher','street','teacher_street']:
 values=summary['stratified'][kind].values();summary[kind+'_balanced_agreement']=sum(v['action_accuracy'] for v in values)/len(summary['stratified'][kind])
for folder,key in [('pete-preflop-select','pre354'),('cleanup-stress-results','cleanup10'),('enum-probes','enum4')]:
 file=E/folder/f'{args.name}.json'
 if not file.exists():summary[key]={'status':'not_available'};continue
 item=json.loads(file.read_text());summary['source_hashes'][str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
 if key=='pre354':
  assert item['status']=='complete' and item['summary']['examples']==354;summary[key]=item['summary']
 elif key=='cleanup10':
  results=[x for x in item['results'] if x is not None];summary[key]={'status':item['status'],'examples':len(results),'valid':sum(bool(x.get('valid')) for x in results),'wrong_tool_calls':sum(x.get('wrong_tool_calls',0) for x in results),'missing_update_calls':sum(x.get('update_call_count',0)==0 for x in results),'overlong':sum((x.get('characters') or 0)>5000 for x in results),'truncated':sum(bool(x.get('truncated')) for x in results),'unknown_argument_keys':sum(bool(x.get('unknown_argument_keys')) for x in results),'scope':'Exact tool protocol only; factual correctness not established.'}
 else:
  # Source file may expose private regression inputs; publish only known aggregate counts.
  results=item.get('results',[]);summary[key]={'status':'complete' if len(results)==4 else 'incomplete','examples':len(results),'legal':sum(bool(x.get('legal')) for x in results),'scope':'Heldout functional enum probes only.'}
checks={'mixed_bet_recall':summary['mixed256']['per_action']['bet']['recall']*27>=7,'mixed_check_recall':summary['mixed256']['per_action']['check']['recall']*43>=39,'mixed_legal':summary['mixed256']['legal_rate']>=.99,'preflop_retention':summary.get('pre354',{}).get('action_accuracy',0)>=.794632768361582,'cleanup_protocol':summary.get('cleanup10',{}).get('valid',0)>=9 and summary.get('cleanup10',{}).get('wrong_tool_calls',0)==0}
summary['frozen_gate_results']=checks;summary['reported_core_gates_pass']=all(checks.values());summary['remaining_gates_not_evaluated_here']=['legacy147postflop retention','cleanup factual correctness','workplace-safe talk before promotion','official paired poker before promotion'];summary['all_required_gates_pass']=False;summary['no_automatic_extension_or_promotion']=True
(R/f'{args.name}-behavior-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['stratified','source_hashes']},indent=2))
