"""Read-only audit of captured genuine replies; no model calls or target repair."""
import json,copy,hashlib
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent
rows=[json.loads(l)for l in(R/'cases.jsonl').open()]
result=json.loads((R/'raw/results-scored.json').read_text());assert result['status']=='complete'
template=Environment().from_string(Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text().replace('{%- generation %}','').replace('{%- endgeneration %}',''));tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json')
canonical=json.loads(Path('/Users/lance/Documents/pokerbots-main/opsd/tools.json').read_text());tools=[{'type':'function','function':{k:v for k,v in x.items()if k!='type'}}for x in canonical]
kw={'tools':tools,'enable_thinking':True,'add_generation_prompt':False,'raise_exception':lambda x:(_ for _ in()).throw(ValueError(x))}
reports=[]
for row,record in zip(rows,result['results']):
 i=row['case'];p=row['original_input'];teacher=copy.deepcopy(p);teacher[0]['content']+='\n\n'+row['teacher_system_only_hint'];wire=[]
 for arm,expected in [('unhinted',p),('hinted',teacher)]:
  req=json.loads((R/f'raw/case{i}-{arm}-request.json').read_text());resp=json.loads((R/f'raw/case{i}-{arm}-response.json').read_text());assert req['messages']==expected;assert req['tools']==tools
  wire.append((req,resp))
 assert {k:v for k,v in wire[0][0].items()if k!='messages'}=={k:v for k,v in wire[1][0].items()if k!='messages'}
 assert wire[0][0]['messages'][1:]==wire[1][0]['messages'][1:]
 v=record['arms']['unhinted'];m=copy.deepcopy(wire[0][1]['choices'][0]['message']);m['role']='assistant'
 for call in m.get('tool_calls')or[]:
  if isinstance(call['function']['arguments'],str):call['function']['arguments']=json.loads(call['function']['arguments'])
 counts=[];errors=[];tails=[]
 for arm,prompt in [('student',p),('teacher',teacher)]:
  try:
   rendered=template.render(messages=prompt+[m],**kw);prefix=template.render(messages=prompt,**(kw|{'add_generation_prompt':True}));tail=rendered[rendered.rfind('<|im_start|>assistant'):];close=tail.count('</think>')==1 and '<tool_call>'in tail and tail.index('</think>')<tail.index('<tool_call>');assert m.get('reasoning_content','').strip()in tail
   counts.append(len(tok.encode(rendered).ids));tails.append({'arm':arm,'closing_think_once_before_tool':close,'prefix_tokens':len(tok.encode(prefix).ids),'fresh_reply_tokens':len(tok.encode(rendered[len(prefix):]).ids) if rendered.startswith(prefix)else None,'render_starts_with_generation_prefix':rendered.startswith(prefix)});(R/f'raw/render-case{i}-{arm}.txt').write_text(rendered)
  except Exception as e:errors.append(type(e).__name__+':'+str(e)[:200])
 usage=[x[1].get('usage',{})for x in wire];delta=usage[1].get('prompt_tokens',0)-usage[0].get('prompt_tokens',0)
 reports.append({'case':i,'wire_student_original_unchanged':True,'wire_teacher_only_system_hint':True,'same_nonmessage_wire_fields':True,'server_prompt_token_delta':delta,'actual_unhinted_reasoning_nonempty':bool(m.get('reasoning_content','').strip()),'actual_reply_complete':v.get('complete',False),'student_total_tokens':counts[0]if len(counts)==2 else None,'teacher_same_unhinted_reply_total_tokens':counts[1]if len(counts)==2 else None,'actual_reply_tokens_response_usage':v.get('out_tokens'),'render':tails,'render_errors':errors})
valid=[x for x in reports if x['student_total_tokens']is not None]
out={'cases':reports,'count':16,'all_wire_hint_placement_pass':True,'all_server_prompt_tokens_increased':all(x['server_prompt_token_delta']>0 for x in reports),'all_retained_replies_complete':all(x['actual_reply_complete']for x in reports),'all_replies_nonempty_genuine_reasoning':all(x['actual_unhinted_reasoning_nonempty']for x in reports),'all_closing_think_before_tool':all(len(x['render'])==2 and all(a['closing_think_once_before_tool']for a in x['render'])for x in reports),'max_student_P_plus_actual_R':max(x['student_total_tokens']for x in valid),'max_teacher_P_plus_same_actual_R':max(x['teacher_same_unhinted_reply_total_tokens']for x in valid),'max_actual_R_usage':max(x['actual_reply_tokens_response_usage']or 0 for x in reports),'max_actual_R_rendered_tokens':max(a['fresh_reply_tokens']or 0 for x in reports for a in x['render']),'context_catalog_limit':32768,'prefix_len_runtime_items':2,'CPU_boundary_only_managed_mask_not_proven':True,'no_reply_fabrication':True,'raw_results_sha256':hashlib.sha256((R/'raw/results-scored.json').read_bytes()).hexdigest()}
(R/'actual-reply-render-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='cases'},indent=2))
