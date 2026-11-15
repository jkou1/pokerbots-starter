"""Render official HF35B template locally; one final supervised reply only."""
import json,hashlib,re
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent
source=Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text();template=Environment().from_string(source.replace('{%- generation %}','').replace('{%- endgeneration %}',''))
tokenizer=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json');samples=[];total={};lengths={};rows=[json.loads(l) for l in (R/'train-tasks.jsonl').open()]
def fail(x):raise ValueError(x)
for idx,task in enumerate(rows):
 inputs=task['input'];assert inputs[-2]['type']=='reasoning' and inputs[-1]['type']=='function_call'
 assert all(x['type']=='message' and x['role'] in ['system','user'] for x in inputs[:-2])
 messages=[{'role':x['role'],'content':x['content']} for x in inputs[:-2]]
 call=inputs[-1];messages.append({'role':'assistant','content':'','reasoning_content':inputs[-2]['content'],'tool_calls':[{'type':'function','function':{'name':call['name'],'arguments':json.loads(call['arguments'])}}]})
 kw={'tools':task['env_params']['tools'],'enable_thinking':True,'raise_exception':fail}
 prompt=template.render(messages=messages[:-1],add_generation_prompt=True,**kw)
 full=template.render(messages=messages,add_generation_prompt=False,**kw)
 assert full.startswith(prompt);target=full[len(prompt):]
 assert prompt.endswith('<think>\n')
 assert target.startswith('Tool call follows.\n</think>') and target.count('</think>')==1
 assert target.count('<tool_call>')==1 and target.count('</tool_call>')==1
 assert f'<function={call["name"]}>' in target
 assert target.index('</think>')<target.index('<tool_call>')
 n=len(tokenizer.encode(target).ids);kind=call['name'];total[kind]=total.get(kind,0)+n
 prompt_tokens=len(tokenizer.encode(prompt).ids);full_tokens=len(tokenizer.encode(full).ids);assert full_tokens<=8192
 lengths.setdefault(kind,{'max_prompt_tokens':0,'max_full_sequence_tokens':0});lengths[kind]['max_prompt_tokens']=max(lengths[kind]['max_prompt_tokens'],prompt_tokens);lengths[kind]['max_full_sequence_tokens']=max(lengths[kind]['max_full_sequence_tokens'],full_tokens)
 if len([x for x in samples if x['tool']==kind])<3:samples.append({'source_index':idx,'tool':kind,'target_tokens':n,'target_sha256':hashlib.sha256(target.encode()).hexdigest(),'one_supervised_reply':True,'boundary_valid':True})
report={'records':len(rows),'official_template_source':'https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/main/chat_template.jinja','template_sha256':hashlib.sha256(source.encode()).hexdigest(),'generation_mask_extension_removed_for_render_only':True,'all_scaffolds_passed':True,'all_have_one_final_supervised_reply':True,'historical_assistant_supervision':False,'target_tokens':total,'rendered_sequence_lengths':lengths,'all_full_sequences_within8192':True,'cleanup_target_token_fraction':total['update_scratchpad']/sum(total.values()),'samples':samples,'managed_backend_render_verification_pending_until_first_update':True}
(R/'local-template-length-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
