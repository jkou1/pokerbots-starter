"""CPU aggregate cached managed tokens; changing batches are not fixed validation."""
import json,gzip,sys,collections,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'pete-postflop-v1'));from action_ce import arguments,summarize
R=Path(__file__).resolve().parent;membership=json.loads((R/'task-membership-map.json').read_text());windows=collections.defaultdict(lambda:collections.defaultdict(list));unique_tasks=set();unique_sources=collections.defaultdict(set);sources=collections.Counter();copies=collections.Counter();errors=[]
for f in sorted((R/'raw').glob('managed-step-*.jsonl.gz')):
 step=int(f.name.split('-')[2].split('.')[0]);w='first10'if step<10 else'last10'
 for l in gzip.open(f,'rt'):
  p=json.loads(l)['payload'];s=membership[p['datapoint_id']];a=arguments(p);windows[w][s['kind']].append(a);sources[s['kind']]+=1;unique_tasks.add(p['datapoint_id']);unique_sources[s['kind']].add(json.dumps(s['source_provenance'],sort_keys=True))
  if s['kind']=='preflop':copies[str(s['sampling_copy'])]+=1
  if {k:a[k]for k in ['action','amount']if k in a}!=s['target']:errors.append('Target mismatch')
state=json.loads((R/'monitor-state.json').read_text());out={'train_id':state['train_id'],'optimizer_updates':state['training_updates'],'source_presentations':dict(sources),'actual_total_presentations':sum(sources.values()),'unique_remote_tasks_observed':len(unique_tasks),'unique_original_source_records_observed':{k:len(v)for k,v in unique_sources.items()},'pre_anchor_copy_presentations':dict(copies),'exact_target_errors':errors,'action_and_amount_CE_windows':{w:{k:summarize(v)for k,v in groups.items()}for w,groups in windows.items()},'planned_weighted_corpus':7369,'actual_weighted_epoch_fraction':sum(sources.values())/7369,'checkpoint_conversions':state['conversions'],'notes':['Protocol text/toolname/parameter syntax excluded from action/amount CE.','First10 and last10 contain different examples; composition and per-class sample counts matter.','Training CE is not fixed validation, convergence, label optimality or poker EV.','No generated V5candidate outcome was used in this report.']};(R/'training-audit-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='action_and_amount_CE_windows'},indent=2))
