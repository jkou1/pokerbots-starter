"""Functional protocol only. Never reports poker rank/EV or chooses a model."""
import hashlib,json,re
from pathlib import Path
from vals_tools.cleanup_score import cleanup_protocol
R=Path('data/experiments/rl20-fallback-functional');receipt=json.loads((R/'receipt.json').read_text());progress=json.loads((R/'progress.json').read_text());job=progress['job_id'];rows=[]
for p in Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs').glob('*.json'):
 raw=p.read_bytes();m=re.search(rb'"relay_job_id"\s*:\s*"([^"]+)"',raw)
 if not m or m[1].decode()!=job:continue
 d=json.loads(raw)
 if not d.get('complete'):continue
 assert d['session_info']['seed']==173873095175117;seat='seat1';actions=[a for h in d['hands']for a in h['actions']if a['player']==seat];cleanups=[x['cleanup']for x in d.get('private',{}).get(seat,{}).get('hands',{}).values()if x.get('cleanup')];cp=cleanup_protocol(cleanups);channel={'legal_real_tool':0,'legal_text_fallback':0,'legal_unexposed':0,'invalid':0};talk=[]
 for a in actions:
  x=a.get('model_response',{});channel['invalid'if x.get('format_error')else'legal_real_tool'if x.get('submitted_by_tool')is True else'legal_text_fallback'if x.get('submitted_by_tool')is False else'legal_unexposed']+=1
  if x.get('say')or x.get('private',{}).get('say_raw'):talk.append({'say':x.get('say'),'raw':x.get('private',{}).get('say_raw')})
 (R/'raw').mkdir(exist_ok=True);(R/'raw'/p.name).write_bytes(raw);rows.append({'session_hands':len(d['hands']),'policy_cleanup_turns':len(cleanups),'policy_actions':len(actions),'channel':channel,'cleanup_protocol':cp,'talk':talk,'source':str(p),'sha256':hashlib.sha256(raw).hexdigest()})
assert len(rows)<=1;report={'scope':'ONEpreviouslyusedTRAINfunctionalcase;no rank/EV/qualityranking/newFINAL','eval_id':receipt['eval_id'],'inference_id':receipt['inference_id'],'checkpoint':receipt['checkpoint'],'status':progress['status'],'complete_games':len(rows),'games':rows};(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
