"""Read-only cached target equality/source weighting and per-kind action CE."""
import json,gzip,sys,time,collections,os
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'pete-postflop-v1'));from action_ce import arguments,summarize
R=Path(__file__).resolve().parent
while datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-15T17:00:00+00:00'):
 try:
  membership=json.loads((R/'task-membership-map.json').read_text());steps={};allstats=collections.defaultdict(list);errors=[]
  for f in sorted((R/'raw').glob('managed-step-*.jsonl.gz')):
   bykind=collections.defaultdict(list);counts=collections.Counter();tokens=collections.Counter();localerrors=[]
   for line in gzip.open(f,'rt'):
    p=json.loads(line)['payload'];source=membership[p['datapoint_id']];a=arguments(p);actual={k:a[k]for k in ['action','amount']if k in a}
    if actual!=source['target']:localerrors.append('Actual managed supervised target differs from original source target')
    kind=source['kind'];counts[kind]+=1;tokens[kind]+=sum(x==1 for x in p['loss_mask']);bykind[kind].append(a);allstats[kind].append(a)
   step=f.name.split('-')[2].split('.')[0];steps[step]={'observed_sequences':sum(counts.values()),'source_counts':dict(counts),'supervised_target_tokens':dict(tokens),'action_ce_by_kind':{k:summarize(v)for k,v in bykind.items()},'exact_target_errors':localerrors};errors+=localerrors
  state=json.loads((R/'monitor-state.json').read_text());out={'updated_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'train_id':state['train_id'],'actual_training_updates':state['training_updates'],'steps':steps,'pooled_action_ce_by_kind':{k:summarize(v)for k,v in allstats.items()},'exact_target_errors':errors,'no_gpu_or_api_calls':True,'not_generation_quality_or_convergence':True};(R/'managed-source-target-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(out['updated_at'],'steps',len(steps),'errors',len(errors),flush=True)
  if len(steps)>=20:break
 except Exception as e:print(type(e).__name__,str(e),flush=True)
 time.sleep(30)
