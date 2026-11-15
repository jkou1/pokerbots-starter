"""CPU V5 coverage+rounded-pot reconciliation. No FINAL, upload or training."""
import json,re,hashlib,copy,random,collections,sys,math
from pathlib import Path
from decimal import Decimal
from ac2.runtime import Task,compute_content_hash
R=Path(__file__).resolve().parent;V=R.parent/'pokerbench-v3';P4=R.parent/'pokerbench-v4';REC=R.parent/'pokerbench-reconciled-off1-v1';sys.path.insert(0,str(V));from audit import ACTION,audit
read=lambda f:[json.loads(l)for l in f.open()];write=lambda f,x:f.write_text(''.join(json.dumps(y,sort_keys=True)+'\n'for y in x));sha=lambda b:hashlib.sha256(b).hexdigest()
def pot(row):
 st={s:200 for s in ['UTG','HJ','CO','BTN','SB','BB']};be={s:0 for s in st};be['SB']=1;be['BB']=2;st['SB']-=1;st['BB']-=2
 for n,section in enumerate(re.split(r'The flop comes|The turn comes|The river comes',row['input'][1]['content'])):
  if n:be={s:0 for s in st}
  for seat,a,num in ACTION.findall(section):
   if a in ['raise','bet']:commit=int(num)-be[seat]
   elif a=='call':commit=min(st[seat],max(be.values())-be[seat])
   else:continue
   assert 0<=commit<=st[seat];st[seat]-=commit;be[seat]+=commit
 return 1200-sum(st.values())
train=read(P4/'train.jsonl')+read(REC/'train.jsonl');tt=read(P4/'train-tasks.jsonl')+read(REC/'train-tasks.jsonl');anchors=read(P4/'preflop-anchors.jsonl');at=read(P4/'preflop-anchor-tasks.jsonl');assert len(train)==3499 and len(anchors)==387
select=read(P4/'select.jsonl');st=read(P4/'select-tasks.jsonl');oldselect=read(V/'fast-select.jsonl');oldst=read(V/'fast-select-tasks.jsonl');off=[];larger=[]
for row,t in zip(oldselect,oldst):
 canonical=pot(row);printed=int(re.search(r'current pot size is (\d+) chips',row['input'][1]['content'])[1]);delta=printed-canonical
 if delta==-1:off.append((row,t,printed,canonical))
 elif delta!=0:larger.append(row['provenance']['source_index'])
needed={r['provenance']['source_index']for r,_,_,_ in off};raw={}
for line in(V.parent/'pokerbench-v2/source.jsonl').open('rb'):
 m=re.search(rb'"source_index"\s*:\s*(\d+)',line)
 if m and int(m[1])in needed:raw[int(m[1])]=json.loads(line)
for old,t,printed,canonical in off:
 new=copy.deepcopy(old);text=old['input'][1]['content'];match=re.search(r'(current pot size is )(\d+)( chips)',text);new['input'][1]['content']=text[:match.start(2)]+str(canonical)+text[match.end(2):];assert audit(new)=='passed';source=raw[old['provenance']['source_index']];literal=re.search(r'current pot size is (\d+(?:\.\d+)?) chips',source['instruction'])[1];assert Decimal(literal)*2==printed;new['provenance']['pot_reconciliation']={'provider_original_printed_pot_literal':literal,'provider_original_target_text':source['output'],'scaled_original_printed_pot':printed,'canonical_decision_time_contribution_sum':canonical,'scaled_target_unchanged':old['target'],'original_v3_row_sha256':sha(json.dumps(old,sort_keys=True).encode()),'derivation':'forcedblindsandexplicitdecision-timecontributions;no inventedhistory','label_status':'unchangedproviderlabelunderroundedsourceinput;nocorrected-stateoptimalityclaim'};task=copy.deepcopy(t);task.pop('id',None);task.pop('content_hash',None);task['input'][1]['content']=new['input'][1]['content'];task['tags']['provenance']=new['provenance'];select.append(new);st.append(task)
assert select[:41]==read(P4/'select.jsonl');assert all(audit(x)=='passed'and pot(x)==int(re.search(r'current pot size is (\d+) chips',x['input'][1]['content'])[1])for x in train+select)
groups={s:{x['provenance']['scenario_group']for x in v}for s,v in [('train',train),('select',select)]};assert not groups['train']&groups['select'];exposed=set(json.loads((R.parent/'pokerbench-pot-semantics-audit/future-final-exclusions.json').read_text())['excluded_scenario_groups']);assert not(exposed&(groups['train']|groups['select']));held=set()
for name in ['select','eval']:
 held|={x['provenance']['match_id']for x in read(R.parent/'mixed-teacher-actions-v1'/f'{name}.jsonl')}
assert not held&{x['provenance']['match_id']for x in anchors}
weighted=copy.deepcopy(tt)
for n in range(10):
 for t in at:
  x=copy.deepcopy(t);x.pop('id',None);x.pop('content_hash',None);x['env_params']['sampling_copy']=n;x['tags']['v5_sampling_source']='unchanged387heldout-safeanchors';weighted.append(x)
random.Random(42).shuffle(weighted);hashes=[compute_content_hash(Task.model_validate(x))for x in weighted];assert len(hashes)==7369 and len(set(hashes))==7369
for name,rows in [('train-postflop',train),('train-postflop-tasks',tt),('weighted-train-tasks',weighted),('select',select),('select-tasks',st)]:write(R/f'{name}.jsonl',rows)
counts=collections.Counter(x['target']['action']for x in select);gates={'N_SELECT':len(select),'additional_exact_vs_parent_min':math.ceil(.073*len(select)),'macro_action_recall_not_worse':True,'combined_bet_raise_examples':counts['bet']+counts['raise'],'combined_bet_raise_matches_min':math.ceil(.30*(counts['bet']+counts['raise'])),'check_call_fold_recall_max_drop_pp':10,'all_select_legal':True,'pre354_action_matches_min':271,'enum_guard_required':True,'cleanup10_protocol_diagnostic_not_memoryfactualmetric':True,'original41_report_separately':True,'officialpairedEV_protocol_workplace_required_before_advancement':True,'candidate_outputs_exist':False};(R/'frozen-gates.json').write_text(json.dumps(gates,indent=2)+'\n');manifest={'stage':'CPUpreparedno upload/trainingyet','train_postflop':{'original_consistent':1060,'reconciled_off1':2439,'total_unique':3499,'larger_mismatches_quarantined':597},'anchors':{'unique':387,'copies_per_source':10,'weighted':3870,'heldout_match_overlap':0},'total':{'unique':3886,'weighted':7369,'weighted_preflop_fraction':3870/7369},'select':{'original41_unchanged_first':41,'reconciled_locked_off1':len(off),'total':len(select),'larger_mismatches_excluded':len(larger),'action_counts':dict(counts),'source':'Onlyoriginal147lockedfastSELECT;nofullselectexpansion'},'original_splits_and_groups_preserved':True,'train_select_group_overlap':0,'exposed_final_group_overlap':0,'final_not_read_uploaded_or_queried':True,'target_label_optimality_after_correction':'uncertain;unchangedproviderlabelunderroundedsourceinput','not_one_factor_ablation':'coverage,roundingreconciliation,weightingandpotentialpilotlength/LRchange','sha256':{p.name:sha(p.read_bytes())for p in R.glob('*.jsonl')}};(R/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2));print('gates',json.dumps(gates))
