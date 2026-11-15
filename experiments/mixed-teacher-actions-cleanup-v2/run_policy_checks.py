"""One served-checkpoint local SELECT check, no deployment/job mutation."""
import argparse,asyncio,os,sys
from pathlib import Path
from dotenv import dotenv_values
sys.path.insert(0,'/tmp');from pokerbots_working_client import preflight_identity
from ac2.sdk import Client
from vals_tools.pete_eval import evaluate
p=argparse.ArgumentParser();p.add_argument('--inference',required=True);p.add_argument('--name',required=True);p.add_argument('--suite',choices=['mixed256','pre354'],required=True);p.add_argument('--concurrency',type=int,default=2);args=p.parse_args()
assert args.inference.startswith('infer_') and 1<=args.concurrency<=4
key=dotenv_values('/Users/lance/Documents/pokerbots-starter/.env').get('AC2_API_KEY');assert key
preflight_identity(Client(project='vals-hackathon',api_key=key));os.environ['AC2_API_KEY']=key
R=Path('/Users/lance/Documents/pokerbots-pokerbench/experiments');records=R/('mixed-teacher-actions-v1/fast-select.jsonl' if args.suite=='mixed256' else 'pete-postflop-v1/preflop-select.jsonl')
out=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments')/('mixed-teacher-select' if args.suite=='mixed256' else 'pete-preflop-select')/f'{args.name}.json'
if out.exists():
 import json
 previous=json.loads(out.read_text())
 if previous.get('status')=='complete':raise SystemExit('Completed fixed check exists; refuse duplicate inference')
print('New-account preflight passed; immutable model',args.inference,'suite',args.suite,'parallel',args.concurrency,flush=True)
a=argparse.Namespace(records=records,model=args.inference,out=out,concurrency=args.concurrency,limit=None)
asyncio.run(asyncio.wait_for(evaluate(a),timeout=400))
