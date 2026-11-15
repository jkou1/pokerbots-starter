"""CPU-only immutable-row consistency curation. Never uploads or trains."""
import json,re,hashlib,collections,random,sys,copy
from pathlib import Path
R=Path(__file__).resolve().parent;V3=R.parent/'pokerbench-v3';P=R.parent/'pete-postflop-v1';sys.path.insert(0,str(V3));from audit import ACTION,audit
from ac2.runtime import Task,compute_content_hash
sha=lambda b:hashlib.sha256(b).hexdigest()
def consistency(row):
 text=row['input'][1]['content'];seats=['UTG','HJ','CO','BTN','SB','BB'];st={s:200 for s in seats};be={s:0 for s in seats};be['SB']=1;be['BB']=2;st['SB']-=1;st['BB']-=2
 if not('Everyone started with 200 chips.'in text and 'small blind is 1 chips and the big blind is 2 chips'in text):return 'unsupported_initial_state'
 for n,section in enumerate(re.split(r'The flop comes|The turn comes|The river comes',text)):
  if n:be={s:0 for s in seats}
  for seat,action,num in ACTION.findall(section):
   if action in ['raise','bet']:commit=int(num)-be[seat]
   elif action=='call':commit=min(st[seat],max(be.values())-be[seat])
   else:continue
   if commit<0 or commit>st[seat]:return 'invalid_stack_transition'
   st[seat]-=commit;be[seat]+=commit
 pot=int(re.search(r'current pot size is (\d+) chips',text)[1])
 if pot!=1200-sum(st.values()):return 'printed_pot_mismatch'
 return 'passed'
def main():
 manifest={'curation':'Input-only canonical monetary replay: initial1200chips,blinds1/2,street-total contributions,stack bounds,printed pot equality. NOT full engine action-order replay. No text/label changes.','source_v3_manifest_sha256':sha((V3/'manifest.json').read_bytes()),'counts':{},'source_hashes':{},'no_upload':True,'no_training':True};out={};taskout={};quarantine={}
 for split,filename in [('train','train'),('select','fast-select'),('final','eval')]:
  rows=[json.loads(l)for l in(V3/f'{filename}.jsonl').open()];tasks=[json.loads(l)for l in(V3/f'{filename}-tasks.jsonl').open()];assert len(rows)==len(tasks);kept=[];kepttasks=[];q=[];reasons=collections.Counter()
  for i,(row,t)in enumerate(zip(rows,tasks)):
   result=consistency(row)
   if result!='passed':reasons[result]+=1;continue
   label=audit(row)
   if label!='passed':q.append({'source_index':i,'source_row_sha256':sha(json.dumps(row,sort_keys=True).encode()),'reason':label});reasons['label_quarantine:'+label]+=1;continue
   kept.append(row);kepttasks.append(t)
  out[split]=kept;taskout[split]=kepttasks;quarantine[split]=q;manifest['counts'][split]={'source':len(rows),'input_consistent':sum(consistency(x)=='passed'for x in rows),'usable':len(kept),'rejected':dict(reasons)};manifest['source_hashes'][split]=sha((V3/f'{filename}.jsonl').read_bytes())
  # Final remains opaque outside this script: no sample/targets/report text.
  (R/f'{split}.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n'for x in kept));(R/f'{split}-tasks.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n'for x in kepttasks));(R/f'{split}-quarantine.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in q))
 assert len(out['train'])==1060
 held=set()
 for split in ['select','eval']:
  for line in(R.parent/'mixed-teacher-actions-v1'/f'{split}.jsonl').open():held.add(json.loads(line)['provenance']['match_id'])
 anchors=[json.loads(l)for l in(P/'mixed-train.jsonl').open()if json.loads(l)['provenance']['street']=='preflop'];anchors=[x for x in anchors if x['provenance']['match_id']not in held];assert len(anchors)==387
 oldtasks=[json.loads(l)for l in(P/'train-tasks.jsonl').open()];lookup={json.dumps(x['tags']['provenance'],sort_keys=True):x for x in oldtasks};at=[lookup[json.dumps(x['provenance'],sort_keys=True)]for x in anchors]
 for split in ['select','eval','preflop-select','preflop-eval']:
  oldheld={json.loads(l)['provenance']['match_id']for l in(P/f'{split}.jsonl').open()};assert not oldheld&{x['provenance']['match_id']for x in anchors}
 (R/'preflop-anchors.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n'for x in anchors));(R/'preflop-anchor-tasks.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n'for x in at))
 weighted=[]
 for t in taskout['train']:weighted.append(t)
 for n in range(3):
  for t in at:
   new=copy.deepcopy(t);new.pop('id',None);new.pop('content_hash',None);new['env_params']['sampling_copy']=n;new.setdefault('tags',{})['v4_sampling_source']='unaltered387preflopanchors';weighted.append(new)
 random.Random(42).shuffle(weighted);hashes=[compute_content_hash(Task.model_validate(t))for t in weighted];assert len(set(hashes))==len(weighted)
 (R/'weighted-train-tasks.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n'for t in weighted));manifest['preflop_anchors']={'unique':387,'matches':len({x['provenance']['match_id']for x in anchors}),'excluded_new_mixed_heldout_matches':6,'old_and_new_holdout_match_overlap':0,'weighted_copies':1161,'copy_metadata_only_in_env_params_not_model_input':True};manifest['training']={'unique':1447,'postflop_unique_and_weighted':1060,'preflop_unique':387,'preflop_weighted':1161,'weighted_total':2221,'preflop_weighted_fraction':1161/2221,'model_input_and_targets_unchanged':True,'target_scaffold':'nonempty protocol marker, not attributed solver private reasoning','cleanup_targets':0};
 groups={s:{x['provenance']['scenario_group']for x in v}for s,v in out.items()}
 for a,b in [('train','select'),('train','final'),('select','final')]:assert not groups[a]&groups[b]
 manifest['split_scenario_group_overlap']=0;manifest['final_policy']='Only count/hash reported; no model calls or final selection. Unsupported labels quarantined without repairs.';manifest['sha256']={x.name:sha(x.read_bytes())for x in R.glob('*.jsonl')};(R/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
