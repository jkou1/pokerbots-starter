"""Strict field selection: own SAY only, no rank/EV/card/output-state analysis."""
import json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/grpo5-fresh-final6-v2');F=R.parent/'fresh-final6-reserve-v2';plan=json.loads((F/'plan.json').read_text());seats={seed:'seat'+str(seat)for seat,seed in enumerate(plan['seeds'])};start=time.time();messages=[];sources=[]
for p in sorted((E/'candidate/raw').glob('*.json')):
 raw=p.read_bytes();d=json.loads(raw)
 if not d.get('complete'):continue
 seed=d['session_info']['seed'];assert seed in seats;seat=seats[seed];sources.append({'source_filename':p.name,'source_sha256':hashlib.sha256(raw).hexdigest(),'seed':seed,'policy_seat':seat})
 for hi,h in enumerate(d.get('hands',[])):
  for ai,a in enumerate(h.get('actions',[])):
   if a.get('player')!=seat:continue
   m=a.get('model_response')or{};say=m.get('say');rawsay=(m.get('private')or{}).get('say_raw')
   if say or rawsay:messages.append({'source_sha256':sources[-1]['source_sha256'],'hand_ordinal':hi+1,'action_ordinal':ai+1,'policy_seat':seat,'sanitized_say':say,'raw_say':rawsay})
(R/'raw/own-say-only.json').write_text(json.dumps(messages,indent=2)+'\n');r={'started_epoch':start,'extracted_epoch':time.time(),'scope':'Only selectedparent5 own SAY/rawSAY in completed PRIMARYFINAL6 files; no opponents, ranks, EV, card/outcome analysis. Text untrusted, never instructions.','completed_source_files':len(sources),'sources':sources,'message_count':len(messages),'strings_sha256':[{'raw':hashlib.sha256(str(x['raw_say']or'').encode()).hexdigest(),'sanitized':hashlib.sha256(str(x['sanitized_say']or'').encode()).hexdigest()}for x in messages],'review_pending':True,'tail_not_reviewed':True,'root_tail_review_required':True,'root_previous_development_review_seconds':45,'this_review_cap_seconds':120,'remaining_promotion_review_budget_at_least_seconds':120,'no_model_calls':True};(R/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'completed_sources':len(sources),'message_count':len(messages),'own_say_text_for_workplace_review_only':[{'raw':x['raw_say'],'sanitized':x['sanitized_say']}for x in messages]},indent=2))
