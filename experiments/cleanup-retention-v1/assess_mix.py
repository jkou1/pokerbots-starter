"""CPU-only protocol-retention recommendation; never alters queued dataset/job."""
import json,hashlib
from pathlib import Path
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent;M=R.parent/'mixed-teacher-actions-v1'
tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json')
def render(r):
 # Estimate standard Qwen managed target rendering; verify actual tokenviz before training.
 return 'Tool call follows.\n</think>\n\n<tool_call>\n<function='+r['tool']+'>\n'+''.join('<parameter='+k+'>\n'+str(v)+'\n</parameter>\n' for k,v in r['target'].items())+'</function>\n</tool_call><|im_end|>'
a=[json.loads(l) for l in (M/'train.jsonl').open()];c=[json.loads(l) for l in (R/'train.jsonl').open()]
counts=lambda rows:[len(tok.encode(render(r)).ids) for r in rows]
at=counts(a);ct=counts(c)
recommend=[]
for copies in [1,20,30,39]:
 n=4*copies;clean_tokens=sum(ct)*copies
 recommend.append({'copies_per_genuine_source':copies,'cleanup_examples':n,'action_examples_preserved':len(a),'example_share':n/(len(a)+n),'estimated_supervised_cleanup_token_share':clean_tokens/(sum(at)+clean_tokens),'expected_cleanup_draws_in_1280':1280*n/(len(a)+n)})
report={'status':'CPU recommendation only; queued job and source dataset unchanged','action_count':len(a),'unique_cleanup_sources':4,'estimated_action_target_tokens':{'mean':sum(at)/len(at),'total':sum(at)},'estimated_cleanup_target_tokens':ct,'tokenizer_source':'https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/main/tokenizer.json','tokenizer_sha256':hashlib.sha256(Path('/tmp/pokerbots-qwen35-tokenizer.json').read_bytes()).hexdigest(),'rendering_caveat':'Standard Qwen target rendering estimate; actual managed target tokenization must be verified before replacement launch.','mix_options':recommend,'preferred_copies_per_source':20,'representation_risk':'Current canonical adapter quotes prior assistant/tool items as user context, preventing historical assistant supervision but differing from runtime. Do not use as if exact conversation. Keep explicitly quoted observed history for this controlled adapter; raw runtime assistant/tool turns must not be used without proven loss masking. Actual runtime serialization mismatch remains a limitation.','no_job_mutation':True}
(R/'PROTOCOL_MIX_ASSESSMENT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
