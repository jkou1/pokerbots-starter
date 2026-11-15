"""Exact original TRAIN pot literal -> Decimal scale trace. No FINAL reads."""
import json,re,hashlib,sys
from pathlib import Path
from decimal import Decimal
R=Path(__file__).resolve().parent;V=R.parent/'pokerbench-v3';sys.path.insert(0,str(V));from prepare import scale
meta=[json.loads(l)for l in(R/'train-monetary-metadata.jsonl').open()];selected=[]
for position in ['HJ','BTN','BB']:
 selected.append(next(x for x in meta if x['printed_minus_canonical']==-1 and x['hero_position']==position))
ids={x['source_index']for x in selected};original={}
for line in(V.parent/'pokerbench-v2/source.jsonl').open('rb'):
 match=re.search(rb'"source_index"\s*:\s*(\d+)',line)
 if match and int(match[1])in ids:
  x=json.loads(line);original[x['source_index']]=x
scaled={x['provenance']['source_index']:x for x in map(json.loads,(V/'train.jsonl').open())if x['provenance']['source_index']in ids};traces=[]
for m in selected:
 x=original[m['source_index']];sourcepot=re.search(r'current pot size is (\d+(?:\.\d+)?) chips',x['instruction'])[1];scaledpot=re.search(r'current pot size is (\d+(?:\.\d+)?) chips',scaled[m['source_index']]['input'][1]['content'])[1];new=scale(x['instruction']);assert re.search(r'current pot size is (\d+) chips',new)[1]==scaledpot;assert Decimal(sourcepot)*2==Decimal(scaledpot);traces.append({'source_index':m['source_index'],'hero_position':m['hero_position'],'source_instruction_sha256':hashlib.sha256(x['instruction'].encode()).hexdigest(),'original_source_pot_literal':sourcepot,'original_source_pot_numeric':str(Decimal(sourcepot)),'canonical_original_contribution_sum':str(Decimal(m['canonical_pot'])/2),'scaled_pot_literal':scaledpot,'canonical_scaled_contribution_sum':m['canonical_pot'],'source_target_unchanged_label':x['output'],'scaled_target':scaled[m['source_index']]['target'],'source_raw_keys':sorted(x),'no_extra_original_numeric_pot_field':True,'rounding_in_converter':False})
report={'scope':'Three locked TRAIN examples only, HJ/BTN/BB','traces':traces,'pipeline':['json.loads preserves instruction string','AMOUNT regex matches numeric chip literal','Decimal(literal)*2','reject unless integral','int() only after integral assertion; no rounding'],'converter_bug_found':False,'finding':'Original source itself prints pot0.5below canonical contribution sum in these examples; exact2x converter preserves the discrepancy. No richer numeric pot field exists in original cached records.','cannot_infer_hidden_source_pot':'Recomputing pot is a new interpretation of the expert state, not recovery of an existing numeric field; cannot promise original expert label stays optimal.','no_repairs_newdata_upload_or_job_changes':True};(R/'scaling-trace.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
