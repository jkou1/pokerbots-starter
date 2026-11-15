import json,hashlib,copy
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent;rows=[json.loads(l)for l in(R/'locked-first10-contexts.jsonl').open()];assert len(rows)==10
source=Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text();template=Environment().from_string(source.replace('{%- generation %}','').replace('{%- endgeneration %}',''));tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json');tools=json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text())
def chat(items):
 out=[]
 for i in items:
  if i['type']=='message':out.append({'role':i['role'],'content':i.get('content','')})
  elif i['type']=='function_call':
   if not out or out[-1]['role']!='assistant':out.append({'role':'assistant','content':''})
   out[-1].setdefault('tool_calls',[]).append({'id':i['call_id'],'type':'function','function':{'name':i['name'],'arguments':json.loads(i['arguments'])}})
  elif i['type']=='function_call_output':out.append({'role':'tool','tool_call_id':i['call_id'],'content':i['output']})
  else:raise ValueError('Unsupported original item, do not quote/clean')
 return out
result=[]
for c in rows:
 p=json.loads(c['original_input_json_exact']);assert p[0]['role']=='system';teacher=copy.deepcopy(p);teacher[0]['content']+='\n\n'+c['teacher_hint'];assert teacher[1:]==p[1:];assert hashlib.sha256(c['original_input_json_exact'].encode()).hexdigest()==c['original_input_sha256']
 kw={'tools':tools,'enable_thinking':True,'add_generation_prompt':True,'raise_exception':lambda x:(_ for _ in()).throw(ValueError(x))};a=template.render(messages=chat(p),**kw);b=template.render(messages=chat(teacher),**kw)
 result.append({'span_id':c['span_id'],'source_match_id':c['source_match_id'],'prefix_items':len(p),'student_tokens':len(tok.encode(a).ids),'hinted_teacher_tokens':len(tok.encode(b).ids),'reply_budget_tokens':10000,'original_input_sha256':c['original_input_sha256'],'hint_sha256':hashlib.sha256(c['teacher_hint'].encode()).hexdigest(),'historical_assistant_tool_items_preserved':True,'only_teacher_system_content_changed':True})
report={'cases':result,'count':10,'max_student_prompt_tokens':max(x['student_tokens']for x in result),'max_teacher_prompt_tokens':max(x['hinted_teacher_tokens']for x in result),'planned_reply_tokens':10000,'max_teacher_prompt_plus_reply_budget':max(x['hinted_teacher_tokens']+10000 for x in result),'original_arena_tools_unavailable_canonical_published_supplied':True,'canonical_tools_sha256':hashlib.sha256(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_bytes()).hexdigest(),'source_jsonl_sha256':hashlib.sha256((R/'locked-first10-contexts.jsonl').read_bytes()).hexdigest(),'no_model_calls':True}
(R/'locked-first10-tokenfit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='cases'},indent=2))
