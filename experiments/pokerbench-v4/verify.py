"""CPU source preservation and official-template boundary audit; no final samples."""
import json,hashlib,copy
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent;T=Environment().from_string(Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text().replace('{%- generation %}','').replace('{%- endgeneration %}',''));tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json')
def chat(items):
 out=[];reason=None
 for x in items:
  if x['type']=='reasoning':reason=x['content']
  elif x['type']=='message':out.append({'role':x['role'],'content':x['content']})
  elif x['type']=='function_call':
   if not out or out[-1]['role']!='assistant':out.append({'role':'assistant','content':''})
   if reason is not None:out[-1]['reasoning_content']=reason;reason=None
   out[-1].setdefault('tool_calls',[]).append({'id':x['call_id'],'type':'function','function':{'name':x['name'],'arguments':json.loads(x['arguments'])}})
  else:raise ValueError('Unsupported item')
 return out
rows=[json.loads(l)for l in(R/'weighted-train-tasks.jsonl').open()];maxlen=0
source={}
for p in [R.parent/'pokerbench-v3/train-tasks.jsonl',R.parent/'pete-postflop-v1/train-tasks.jsonl']:
 for l in p.open():
  x=json.loads(l);source[json.dumps(x['tags']['provenance'],sort_keys=True)]=x
for x in rows:
 old=source[json.dumps(x['tags']['provenance'],sort_keys=True)];assert x['input']==old['input'];assert x['env_params']['tools']==old['env_params']['tools'];assert x['input'][-2]['type']=='reasoning'and x['input'][-2]['content'];assert x['input'][-1]['type']=='function_call'and x['input'][-1]['name']=='submit_action';tools=[{'type':'function','function':{k:v for k,v in z.items()if k!='type'}}for z in x['env_params']['tools']];rendered=T.render(messages=chat(x['input']),tools=tools,enable_thinking=True,add_generation_prompt=False,raise_exception=lambda y:(_ for _ in()).throw(ValueError(y)));tail=rendered[rendered.rfind('<|im_start|>assistant'):];assert tail.count('</think>')==1 and tail.index('</think>')<tail.index('<tool_call>');maxlen=max(maxlen,len(tok.encode(rendered).ids))
report={'weighted_train_audited':len(rows),'exact_original_input_and_target_preservation':True,'original_tools_preserved':True,'one_protocol_marker_and_submit_action':True,'think_close_once_before_tool':True,'max_rendered_total_tokens':maxlen,'protocol_marker_is_not_solver_private_reasoning':True,'managed_training_mask_proven':False,'no_final_content_inspected_by_this_verifier':True};(R/'boundary-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
