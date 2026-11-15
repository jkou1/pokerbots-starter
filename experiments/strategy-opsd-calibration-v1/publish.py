"""Publish aggregate LOCAL calibration, not a fabricated native evaluation."""
import json,sys,hashlib,httpx
from pathlib import Path
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
R=Path(__file__).resolve().parent;c=working_client();identity=preflight_identity(c);slug='strategy-opsd-calibration-v1'
try:coll=c.collections.get_by_slug(slug=slug)
except httpx.HTTPStatusError as e:
 if e.response.status_code!=404:raise
 preflight_identity(c);coll=c.collections.create(slug=slug,name='Strategy OPSD BASE calibration — CLOSED negative',description='LOCAL16TRAINpairs/32calls,notnativeEvalorEV;teacher-onlyexpert-actionhints,frozen14/16,+4,alllegalcompletegatefailed.NoOPSDtraining.')
p=R/'publication.json';receipt=json.loads(p.read_text())if p.exists()else{'collection_id':coll.id,'slug':slug,'identity':identity,'artifacts':{}}
for name in ['FRAMEWORK.md','manifest.json','tokenfit.json','probe-policy.json','summary.json','actual-reply-render-audit.json','CONCLUSION.md']:
 if name in receipt['artifacts']:continue
 preflight_identity(c);a=c.artifacts.upload(R/name,collection=slug);receipt['artifacts'][name]={'id':a.id,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest(),'state':a.state};p.write_text(json.dumps(receipt,indent=2)+'\n');print(name,a.id,flush=True)
print(coll.id)
