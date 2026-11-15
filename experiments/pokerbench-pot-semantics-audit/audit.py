"""TRAIN-only read-only monetary semantics evidence, no dataset repair."""
import json,re,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;V=R.parent/'pokerbench-v3';rows=[json.loads(l)for l in(V/'train.jsonl').open()];A=re.compile(r'\b(UTG|HJ|CO|BTN|SB|BB) (raise|bet|call|check|fold)(?: (\d+))?');results=[];positions=collections.defaultdict(collections.Counter)
for row in rows:
 text=row['input'][1]['content'];seats=['UTG','HJ','CO','BTN','SB','BB'];st={s:200 for s in seats};bets={s:0 for s in seats};bets['SB']=1;bets['BB']=2;st['SB']-=1;st['BB']-=2;hero=re.search(r'your position is (UTG|HJ|CO|BTN|SB|BB)',text)[1];actors={hero};folded=set();turns=[]
 for n,section in enumerate(re.split(r'The flop comes|The turn comes|The river comes',text)):
  if n:bets={s:0 for s in seats}
  for seat,action,num in A.findall(section):
   actors.add(seat)
   if action=='fold':folded.add(seat);continue
   if action in ['raise','bet']:commit=int(num)-bets[seat]
   elif action=='call':commit=min(st[seat],max(bets.values())-bets[seat])
   else:continue
   st[seat]-=commit;bets[seat]+=commit;turns.append((seat,action,commit))
 implicit=set(seats)-actors;folded|=implicit;contrib={s:200-st[s]for s in seats};canonical=sum(contrib.values());printed=int(re.search(r'current pot size is (\d+) chips',text)[1]);dead=sum(contrib[s]for s in folded);delta=printed-canonical;positions['all'][hero]+=1;positions['consistent'if delta==0 else'mismatch'][hero]+=1
 results.append({'source_index':row['provenance']['source_index'],'source_row_sha256':row['provenance']['source_sha256'],'hero_position':hero,'printed_pot':printed,'canonical_pot':canonical,'printed_minus_canonical':delta,'folded_dead_contributions':dead,'printed_equals_active_only':printed==canonical-dead,'printed_equals_floor_to_even_scaled_chips':printed==canonical-(canonical%2),'contributions':contrib,'implicit_folded':sorted(implicit),'explicit_or_implicit_folded':sorted(folded)})
mis=[x for x in results if x['printed_minus_canonical']];off1=[x for x in mis if x['printed_minus_canonical']==-1];examples=[]
for delta in [-1,-3,-5,-10,-27]:
 candidates=[x for x in results if x['printed_minus_canonical']==delta];examples+=candidates[:2]
report={'scope':'Existing4096TRAIN only; no SELECT/FINAL/outputs/models changed','rows':len(rows),'position_counts':{k:dict(v)for k,v in positions.items()},'delta_counts':dict(collections.Counter(str(x['printed_minus_canonical'])for x in results)),'mismatch_rows':len(mis),'off1_rows':len(off1),'off1_matches_active_only':sum(x['printed_equals_active_only']for x in off1),'off1_matches_floor_original_halfchip':sum(x['printed_equals_floor_to_even_scaled_chips']for x in off1),'all_mismatches_active_only_explained':sum(x['printed_equals_active_only']for x in mis),'larger_mismatch_deadmoney_explained':sum(x['printed_equals_active_only']for x in mis if x['printed_minus_canonical']!=-1),'examples_metadata_only':examples,'interpretation_limits':'Active-onlypot and originalhalfchipfloor explanations observationally coincide on manyoff1rows. Need explicit originalsource displayevidence, not infer solverlabelsemantics. No full engine action-order replay.','no_repairs_or_new_data':True};(R/'train-monetary-metadata.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in results));(R/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='examples_metadata_only'},indent=2))
# Exact few TRAIN source observations retained locally only; never FINAL.
selected={x['source_index']for x in examples};source=V.parent/'pokerbench-v2/source.jsonl';raw=[]
for line in source.open('rb'):
 m=re.search(rb'"source_index"\s*:\s*(\d+)',line)
 if m and int(m[1])in selected:raw.append(line.decode())
(R/'raw').mkdir(exist_ok=True);(R/'raw/train-examples-original-source.jsonl').write_text(''.join(raw));(R/'raw/train-examples-v3.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in rows if x['provenance']['source_index']in selected));print('original TRAINexamples saved',len(raw))
