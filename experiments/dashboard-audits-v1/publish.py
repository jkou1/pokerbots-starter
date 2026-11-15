"""Publish audits as native AC2 artifacts/collection, never synthetic eval records."""
import base64,dataclasses,hashlib,json,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
import httpx
sys.path.insert(0,'/tmp')
from pokerbots_working_client import working_client,preflight_identity
ROOT=Path(__file__).resolve().parent
SLUG='poker-sft-action-audits-20261115'
FILES=['READ_ME_FIRST.md','ACTION_TOKEN_CE.png','ACTION_TOKEN_CE.svg','continuation-action-ce.json','base-action-ce.json','LOCAL_EVALUATION_SUMMARIES.json','NATIVE_EVAL_REFERENCES.json','EARLY_STOP_REVIEW.md','first-update-paired-audit.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# User override after initial publication: all future writes use the newly
# configured lmathias account. Never fall back to recovered harness credentials.
c=working_client()
identity=preflight_identity(c)
headers=c._token_manager.auth_headers()
token=headers.get('Authorization',headers.get('authorization','')).split()[-1]
claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
if claims.get('email')!='lmathias@berkeley.edu' or claims.get('org_id')!='org_cd68943dd947' or claims.get('sub')!='usr_fe87402bc9fc':
 raise RuntimeError('Publication requires the newly authorized lmathias identity; no fallback allowed')
try:collection=c.collections.get_by_slug(slug=SLUG)
except httpx.HTTPStatusError as e:
 if e.response.status_code!=404:raise
 collection=c.collections.create(slug=SLUG,name='Poker SFT action audits and LOCAL diagnostics — Nov15',description='Action-only CE audits for two existing SFT runs. LOCAL147postflop/354preflopdiagnostics are artifacts, not native Eval runs. Also links two genuine32task native platform evals. Training CE is not poker performance. No new GPU work.')
train_ids=['train_e3fba0323bd2','train_4cc69b58d8e9']
eval_ids=['eval_521f73148d31','eval_7353b52d4873']
c.collections.add_train_runs(collection_id=collection.id,ids=train_ids)
c.collections.add_eval_runs(collection_id=collection.id,ids=eval_ids)
manifest={'created_at':datetime.now(timezone.utc).isoformat(),'collection_id':collection.id,'collection_slug':SLUG,'train_ids':train_ids,'native_eval_ids':eval_ids,'local_diagnostics_are_native_evals':False,'sha256':{n:sha(ROOT/n) for n in FILES}}
(ROOT/'BUNDLE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(ROOT/'AUDIT_BUNDLE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in FILES+['BUNDLE_MANIFEST.json']:z.write(ROOT/name,arcname=name)
p=ROOT/'publication.json';receipt=json.loads(p.read_text()) if p.exists() else {'collection':collection.model_dump(mode='json'),'artifacts':{}}
for name in ['READ_ME_FIRST.md','ACTION_TOKEN_CE.png','continuation-action-ce.json','base-action-ce.json','LOCAL_EVALUATION_SUMMARIES.json','NATIVE_EVAL_REFERENCES.json','AUDIT_BUNDLE.zip']:
 if name in receipt['artifacts']:
  if receipt['artifacts'][name]['sha256']!=sha(ROOT/name):raise ValueError('Existing published snapshot differs; use a new version')
  continue
 artifact=c.artifacts.upload(ROOT/name,collection=SLUG)
 receipt['artifacts'][name]={'id':artifact.id,'state':artifact.state,'source_name':artifact.source_name,'size_bytes':artifact.size_bytes,'sha256':sha(ROOT/name),'collection_ids':artifact.collection_ids}
 p.write_text(json.dumps(receipt,indent=2)+'\n')
 print(name,artifact.id,artifact.state,artifact.size_bytes,flush=True)
actual=c.artifacts.list(collection_id=collection.id,limit=100)
expected={v['id'] for v in receipt['artifacts'].values()}
assert expected<={r.id for r in actual}
for ident in train_ids:
 row=c._require_api().request('GET',f'/train/{ident}').json()
 assert collection.id in row['collection_ids']
for ident in eval_ids:
 row=c._require_api().request('GET',f'/eval/{ident}').json()
 assert collection.id in row['collection_ids']
bundle_id=receipt['artifacts']['AUDIT_BUNDLE.zip']['id'];download=Path('/tmp/poker-sft-audit-bundle-verified.zip')
c.artifacts.download(bundle_id,download)
assert sha(download)==sha(ROOT/'AUDIT_BUNDLE.zip')
receipt.update(verified_at=datetime.now(timezone.utc).isoformat(),verified_artifact_membership=True,verified_train_membership=True,verified_eval_membership=True,verified_download_sha256=sha(download),train_dashboard_urls={ident:c._console_org_url(f'p/prj_ba36d29befaf/observability/training/{ident}') for ident in train_ids})
p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'collection_id':collection.id,'slug':SLUG,'artifacts':{k:v['id'] for k,v in receipt['artifacts'].items()},'verified_download':True},indent=2))
