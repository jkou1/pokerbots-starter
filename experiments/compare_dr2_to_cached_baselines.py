"""CPU-only paired native artifact comparison; refuses incomplete selection data."""
import json,statistics,argparse
from pathlib import Path
from vals_tools.game_score import bootstrap
R=Path('data/experiments/late-grpo-fresh64-v1')
def load(label):
 r=json.loads((R/label/'native-artifacts.json').read_text());assert r['status']=='succeeded'and len(r['tasks'])==64 and all(x['ev_bb']is not None for x in r['tasks'].values());return r['tasks']
parser=argparse.ArgumentParser();parser.add_argument('--label',default='base-dr2');a=parser.parse_args();candidate=load(a.label);out={}
for label in['step20','catalog-base']:
 baseline=load(label);assert candidate.keys()==baseline.keys();d=[candidate[k]['ev_bb']-baseline[k]['ev_bb']for k in sorted(candidate)];strata={}
 for opp in['ad74','base20']:
  v=[candidate[k]['ev_bb']-baseline[k]['ev_bb']for k in sorted(candidate)if candidate[k]['opponent_stratum']==opp];assert len(v)==32;strata[opp]={'pairs':32,'mean_gain_bb':statistics.fmean(v),'ci95':bootstrap(v)}
 out[label]={'pairs':64,'mean_gain_bb':statistics.fmean(d),'ci95':bootstrap(d),'strata':strata}
(R/(a.label+'-vs-both.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
