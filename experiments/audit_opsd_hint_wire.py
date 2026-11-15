import json,hashlib,copy
from pathlib import Path
from jinja2 import Environment

r=Path('/Users/lance/Documents/pokerbots-pokerbench/experiments/c-arena-cleanup-opsd-v2-rl20');rows=[json.loads(x)for x in(r/'locked-first10-contexts.jsonl').read_text().splitlines()];requests=[(p,json.loads(p.read_text()))for p in(r/'raw').glob('http-*-request.json')];source=Path('/tmp/pokerbots-qwen35-chat-template.jinja').read_text();template=Environment().from_string(source.replace('{%- generation %}','').replace('{%- endgeneration %}',''));results=[]
for i,row in enumerate(rows,1):
 hint=row['teacher_hint'];matches=[(p,q)for p,q in requests if hint in q['messages'][0].get('content','')];assert len(matches)==1,(i,len(matches));p,q=matches[0];s=q['messages'][0];assert set(s)=={'role','content'}and s['role']=='system';assert q['chat_template_kwargs']=={'enable_thinking':True};normalized=copy.deepcopy(q['messages']);
 for msg in normalized:
  for call in msg.get('tool_calls',[]):
   if isinstance(call['function']['arguments'],str):call['function']['arguments']=json.loads(call['function']['arguments'])
 render=template.render(messages=normalized,tools=q['tools'],enable_thinking=True,add_generation_prompt=True,raise_exception=lambda x:(_ for _ in()).throw(ValueError(x)));assert hint in render
 # Teacher system hint must occur before first end-of-system token.
 assert render.index(hint)<render.index('<|im_end|>');plain=copy.deepcopy(q);plain['messages'][0]['content']=plain['messages'][0]['content'].removesuffix('\n\n'+hint);partners=[p0 for p0,q0 in requests if q0==plain];assert len(partners)==1,(i,'no exact unhinted body partner')
 results.append({'case':i,'request':str(p),'request_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'system_keys':list(s),'hint_in_canonical_content':True,'hint_in_rendered_system':True,'hinted_prompt_render_characters':len(render),'only_body_difference_is_system_hint':True,'unhinted_request':str(partners[0]),'no_messages_override_or_dual_text_field':True})
out={'scope':'Read-only actual HTTP request JSON + cached catalog HF template; no live engine renderer introspection, model calls or mutation. Historical tool-call arguments JSON-decoded for HF mapping renderer; original wire retained and compared. Gateway internal parser not observed, hint visibility independent of argument parsing.','template_sha256':hashlib.sha256(source.encode()).hexdigest(),'cases':results,'all10_hint_visible':True,'no_extra_model_calls':True};p=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/native-offline-cleanup-opsd-v1/rl20-wire-hint-audit.json');p.write_text(json.dumps(out,indent=2)+'\n');print('all10_hint_visible_system_content_rendered; exact_body_partner10; nooverride')
