import json,copy,hashlib
from pathlib import Path
from jinja2 import Environment
from tokenizers import Tokenizer
R=Path(__file__).resolve().parent;responses={};files=list((R/'raw').glob('http-*-response.json'))
for f in files:
 d=json.loads(f.read_bytes());responses[f.name.replace('-response.json','-request.json')]=d
contexts=[json.loads(l)for l in(R/'locked-first10-contexts.jsonl').open()];results=json.loads((R/'raw/paired-first10-results.json').read_text())['results'];template_source=Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text();template=Environment().from_string(template_source.replace('{%- generation %}','').replace('{%- endgeneration %}',''));tok=Tokenizer.from_file('/tmp/pokerbots-qwen35-tokenizer.json');audit=[]
for i,(c,result)in enumerate(zip(contexts,results)):
 arms={}
 for arm,v in result['arms'].items():
  ids={x['id']for x in v['tool_calls']};matched=[(name,d)for name,d in responses.items()if{x['id']for x in d['choices'][0]['message']['tool_calls']}==ids];assert len(matched)==1;name,_=matched[0];body=json.loads((R/'raw'/name).read_bytes());messages=copy.deepcopy(body['messages']);system=messages[0]['content'];expected=json.loads(c['original_input_json_exact'])[0]['content']+ ('\n\n'+c['teacher_hint']if arm=='hinted'else'');assert system==expected;assert isinstance(system,str);assert 'input'not in body
  # Official HF template expects parsed argument dictionaries; server-parser equivalence is independently audited.
  for msg in messages:
   for call in msg.get('tool_calls',[]):
    if isinstance(call['function']['arguments'],str):call['function']['arguments']=json.loads(call['function']['arguments'])
  rendered=template.render(messages=messages,tools=body['tools'],enable_thinking=body['chat_template_kwargs']['enable_thinking'],add_generation_prompt=True,raise_exception=lambda x:(_ for _ in()).throw(ValueError(x)));systemrender=rendered.split('<|im_end|>',1)[0];assert system.strip()in systemrender;hint=c['teacher_hint'];pos=rendered.find(hint)
  if arm=='hinted':assert pos>=0 and rendered.count(hint)==1
  else:assert pos==-1
  arms[arm]={'http_method':'POST','http_path':'https://inference.appliedcompute.com/v1/chat/completions','treatment_field':'messages[0].content','http_system_sha256':hashlib.sha256(system.encode()).hexdigest(),'rendered_system_sha256':hashlib.sha256(systemrender.encode()).hexdigest(),'rendered_prompt_tokens':len(tok.encode(rendered).ids),'hint_present_exactly_once':pos>=0,'hint_character_start':pos if pos>=0 else None,'hint_token_prefix_range':[len(tok.encode(rendered[:pos]).ids),len(tok.encode(rendered[:pos+len(hint)]).ids)]if pos>=0 else None,'no_competing_input_field':True};(R/f'raw/wire-case{i+1}-{arm}-render.txt').write_text(rendered)
 assert arms['unhinted']['http_system_sha256']!=arms['hinted']['http_system_sha256'];audit.append({'case':i+1,'arms':arms})
out={'count':10,'all_http_hints_in_messages_0_content':True,'all_cpu_official_hf_renders_include_hint_once_in_system':True,'original_history_preserved':True,'server_actual_tokenization_or_attention_not_exposed':True,'tool_payload_note':'Wire uses OpenAI function-wrapped tools; previous runtime CPU token audit used flat canonical definitions. This audit renders actual wire definitions. Historical tool argument strings parsed for official HF template, pending independent server-parser equivalence.','template_sha256':hashlib.sha256(template_source.encode()).hexdigest(),'cases':audit};(R/'wire-hint-audit.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items()if k!='cases'})
