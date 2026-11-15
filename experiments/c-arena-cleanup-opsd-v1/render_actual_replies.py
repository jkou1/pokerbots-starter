import json,copy
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent;template=Environment().from_string(Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text().replace('{%- generation %}','').replace('{%- endgeneration %}',''));tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json');tools=json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text());results=json.loads((R/'raw/paired-first10-results.json').read_text())['results'];report=[]
def chat(items):
 out=[];pending=None
 for x in items:
  if x['type']=='reasoning':pending=x['content']
  elif x['type']=='message':
   msg={'role':x['role'],'content':x.get('content','')}
   if pending is not None:assert x['role']=='assistant';msg['reasoning_content']=pending;pending=None
   out.append(msg)
  elif x['type']=='function_call':
   if not out or out[-1]['role']!='assistant':out.append({'role':'assistant','content':''})
   if pending is not None:out[-1]['reasoning_content']=pending;pending=None
   out[-1].setdefault('tool_calls',[]).append({'id':x['call_id'],'type':'function','function':{'name':x['name'],'arguments':json.loads(x['arguments'])}})
  elif x['type']=='function_call_output':out.append({'role':'tool','tool_call_id':x['call_id'],'content':x['output']})
  else:raise ValueError(x['type'])
 assert pending is None;return out
for i,case in enumerate(results):
 v=case['arms']['unhinted'];p=v['input_runtime_items'];reply=v['runtime_items_exact'];assert reply[0]['type']=='reasoning'and reply[0]['content'];original=chat(p);new=chat(reply);assert len(new)==1;assert new[0]['reasoning_content']==v['reasoning'];teacher=copy.deepcopy(original);teacher[0]['content']+='\n\n'+case['hint'];kw={'tools':tools,'enable_thinking':True,'add_generation_prompt':False,'raise_exception':lambda x:(_ for _ in()).throw(ValueError(x))}
 counts=[]
 for arm,prompt in [('student',original),('teacher',teacher)]:
  rendered=template.render(messages=prompt+new,**kw);tail=rendered[rendered.rfind('<|im_start|>assistant'):];assert tail.count('</think>')==1 and tail.index('</think>')<tail.index('<tool_call>');assert v['reasoning'].strip()in tail;counts.append(len(tok.encode(rendered).ids));(R/f'raw/render-case{i+1}-{arm}.txt').write_text(rendered)
 report.append({'case':i+1,'original_prefix_items':len(p),'fresh_reply_items':len(reply),'actual_reasoning_preserved':True,'close_think_once_before_tool':True,'student_total_tokens':counts[0],'teacher_total_tokens':counts[1],'prefix_loss_mask_claim':'CPU boundary only; managed token mask NOT proved'})
out={'cases':report,'max_student_total':max(x['student_total_tokens']for x in report),'max_teacher_total':max(x['teacher_total_tokens']for x in report),'managed_mask_proof':False,'no_reply_fabrication':True};(R/'actual-reply-render-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='cases'}))
