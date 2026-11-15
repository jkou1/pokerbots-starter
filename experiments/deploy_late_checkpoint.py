"""Create only an approved one-GPU late checkpoint deployment after explicit clearance."""
import argparse,hashlib,json,os,time
from pathlib import Path
from ac2.sdk import Client,ScalingConfig
from ac2.sdk.model import ModelConfig
from pokerbots_working_client import preflight_identity
p=argparse.ArgumentParser();p.add_argument('--label',choices=['step100','step95','step90','step40','own-b5'],required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--capacity-receipt',type=Path,required=True);a=p.parse_args();ROOT=Path(__file__).resolve().parent.parent/'data/experiments/late-grpo-fresh64-v1';clearance=json.loads(a.capacity_receipt.read_text());required=['diagnostic_six_gpus_released','root_own_b5_baseline_approved','protected_serving_verified']if a.label=='own-b5'else['grpo_gpus_released','mixed_four_gpus_running','final_requests_drained','protected_serving_verified'];assert all(clearance.get(k)is True for k in required)
if a.label=='step95':assert clearance.get('root_fallback95_approved')is True,'No implicit95 fallback'
if a.label=='step90':assert clearance.get('root_fallback90_approved')is True,'No implicit90 fallback'
out=ROOT/'serving';out.mkdir(exist_ok=True);path=out/(a.label+'.json');c=Client(project='vals-hackathon',api_key=os.environ['AC2_API_KEY']);identity=preflight_identity(c)
if path.exists():
 r=json.loads(path.read_text());assert r['checkpoint']==a.checkpoint;print(json.dumps(r));raise SystemExit
assert str(c.checkpoints.promotion_status(a.checkpoint).state).lower()=='available'
for mid,pin in clearance['protected_pins'].items():
 live=c.inference.get(mid);assert live.checkpoint_id==pin['checkpoint']and live.version==pin['version']and live.state in ['ready','running','healthy']
name='grpo-history-ad74-'+a.label;existing=[d for d in c.inference.list()if d.name==name and d.state!='deleted']
if existing:raise RuntimeError('Matching existing request lacks local receipt; inspect before any duplicate deployment')
# No scaling/cluster/engine override: the same proven catalog checkpoint serving path, exactly one replica.
preflight_identity(c);mid=c.inference.deploy(name=name,model=ModelConfig(checkpoint=a.checkpoint),scaling=ScalingConfig(min_replicas=1,max_replicas=1));r={'label':a.label,'inference_id':mid,'model':'vals-hackathon/'+name,'checkpoint':a.checkpoint,'requested_at':time.time(),'scaling':{'min_replicas':1,'max_replicas':1},'identity_preflight':identity,'capacity_receipt':str(a.capacity_receipt.resolve()),'capacity_receipt_sha256':hashlib.sha256(a.capacity_receipt.read_bytes()).hexdigest(),'ready_verified':False};path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
