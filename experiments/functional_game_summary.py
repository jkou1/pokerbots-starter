"""Audit one LOCAL-default-schema functional game; never read sealed final games."""
import hashlib,json,os,re
from pathlib import Path
from ac2.sdk import Client
from poker_harness.grading import seat_result
from vals_tools.cleanup_score import cleanup_protocol
root=Path(__file__).resolve().parent.parent/'data/experiments/fullschema-functional30/rl20';r=json.loads((root/'receipt.json').read_text());c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);run=c.eval.get(r['eval_id']);result={'eval_id':r['eval_id'],'job_id':run.job_id,'status':run.status,'scope':'One fresh LOCAL-default-schema functional smoke. Optional p_win/read extend the documented Arena action/amount/say interface; live Arena server code not retrieved. No poker performance conclusion.','effective_submit_fields':r['effective_submit_fields'],'completed_games':0}
for path in Path('/Users/lance/Documents/pokerbots-starter-grpo-history/harness/runs').glob('*.json'):
 raw=path.read_bytes();job=re.search(rb'"relay_job_id"\s*:\s*"([^"]+)"',raw)
 if not job or job.group(1).decode()!=run.job_id:continue
 log=json.loads(raw)
 if not log.get('complete'):continue
 assert log['session_info']['seed']==r['seed'];assert result['completed_games']==0
 seat='seat'+str(r['policy_seat']);graded=seat_result(log,[seat]);cleanups=[h['cleanup'] for h in log.get('private',{}).get(seat,{}).get('hands',{}).values() if h.get('cleanup')];actions=[a for h in log['hands'] for a in h['actions'] if a['player']==seat];talk=[{'say':a['model_response'].get('say'),'raw':a['model_response'].get('private',{}).get('say_raw')} for a in actions if a['model_response'].get('say') or a['model_response'].get('private',{}).get('say_raw')];(root/'raw').mkdir(exist_ok=True);(root/'raw'/path.name).write_bytes(raw)
 result.update(completed_games=1,policy_decisions=graded.decisions,invalid_decisions=graded.format_errors,hands=graded.hands,cleanup_protocol=cleanup_protocol(cleanups),talk=talk,errors=[{'street':a['street'],'error':a['model_response'].get('error')} for a in actions if a['model_response'].get('format_error')],source={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
(root/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
