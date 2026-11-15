"""Submit coordinator-approved, fully verified continuation pilot once."""
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from ac2.sdk import Client
from ac2.sdk.run_config import RunConfig
ROOT=Path(__file__).resolve().parent
receipt=ROOT/'base-control-run.json'
if receipt.exists() and json.loads(receipt.read_text()).get('train_id'):raise SystemExit('Run already submitted; refuse duplicate.')
upload=json.loads((ROOT/'upload.json').read_text())
assert all(upload[s]['status']=='verified' for s in ['train','select','eval'])
c=Client(project='vals-hackathon')
config=json.loads((ROOT/'base-control-config.json').read_text())
manifest={'status':'prepared','config':config,'data_manifest_sha256':hashlib.sha256((ROOT/'quality.json').read_bytes()).hexdigest(),'experiment_framework_sha256':hashlib.sha256((ROOT/'EXPERIMENT.md').read_bytes()).hexdigest(),'upload_receipt_sha256':hashlib.sha256((ROOT/'upload.json').read_bytes()).hexdigest(),'created_at':datetime.now(timezone.utc).isoformat()}
receipt.write_text(json.dumps(manifest,indent=2)+'\n')
run=c.train.run(RunConfig.from_json(config))
manifest.update(status='submitted',train_id=run.train_id)
receipt.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'train_id':run.train_id,'gpus':4,'steps':40,'dataset':upload['train']['name']}))
