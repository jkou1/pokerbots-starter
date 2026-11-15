"""Known supported native span query; read-only, only this development evaluation."""
import json,sys,gzip,os,time
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;os.umask(0o077);c=working_client();identity=preflight_identity(c)
spans=c.analytics.spans(run_ids=['eval_c86991deffcc']).select('input','output','span_id','trace_id','start_time','datapoint_id').filter(name='get_completion').to_records()
p=R/'raw/parent5-visible-spans.jsonl.gz';tmp=p.with_suffix('.tmp')
with gzip.open(tmp,'wt')as f:
 for s in spans:f.write(json.dumps(s,sort_keys=True)+'\n')
tmp.replace(p);(R/'fetch-status.json').write_text(json.dumps({'read_only':True,'eval_id':'eval_c86991deffcc','count':len(spans),'at_epoch':time.time(),'identity':identity,'no_model_calls':True},indent=2)+'\n');print('spans',len(spans),flush=True)
