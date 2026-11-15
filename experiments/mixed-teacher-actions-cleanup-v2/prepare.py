import json,random,sys,hashlib,collections
from pathlib import Path
sys.path.insert(0,'/Users/lance/Documents/pokerbots-main')
from vals_tools.training import supervised_task
R=Path(__file__).resolve().parent;A=R.parent/'mixed-teacher-actions-v1';C=R.parent/'cleanup-retention-v1'
a=[json.loads(l) for l in (A/'train.jsonl').open()];c=[json.loads(l) for l in (C/'train.jsonl').open()]
assert len(a)==7640 and len(c)==4
rows=list(a)
for copy in range(20):
 for idx,original in enumerate(c):
  row=json.loads(json.dumps(original));row['sampling_copy']=copy;row['provenance']['control_kind']='genuine-own-cleanup-retention';row['provenance']['source_index']=idx;row['provenance']['sampling_copy']=copy;rows.append(row)
random.Random(42).shuffle(rows)
(R/'train.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
tasks=[supervised_task(r) for r in rows]
assert len({t.content_hash for t in tasks})==7720
(R/'train-tasks.jsonl').write_text(''.join(t.model_dump_json()+'\n' for t in tasks))
kind=lambda r:r['provenance'].get('teacher','genuine-own-cleanup')
prefix={str(n):dict(collections.Counter(kind(r) for r in rows[:n])) for n in [128,256,640,1280]}
assert set(prefix['1280'])=={'house-professor-pete','house-chatty-carlos','genuine-own-cleanup'}
(R/'prefix-balance.json').write_text(json.dumps(prefix,indent=2)+'\n')
cfg=json.loads((A/'proposed-config.json').read_text());cfg['name']='mixed-pete-carlos-actions-cleanup-v2-base-sft-10steps-b128';cfg['description']='Same7640legalPeteCarlosactions+80copiesof4genuinevalidatedowncleanupTRAINreplies;protocolretentionbugfix;10updates;checkpoint5/10;noautomaticextension.';cfg['tags']['dataset']='pokerbots-mixed-pete-carlos-actions-cleanup-v2-train';cfg['tags']['protocol_retention']='4genuine_sources80copies';cfg['experiment_cfg']['tasks']['datasets'][0]['ac2_dataset_name']=cfg['tags']['dataset'];(R/'proposed-config.json').write_text(json.dumps(cfg,indent=2)+'\n')
p=json.loads((R/'STOP_AND_EXTENSION_POLICY.json').read_text());p['cleanup_protocol_gate']={'heldout_inputs':10,'minimum_exact_valid_update_scratchpad':9,'maximum_submit_action_during_cleanup':0,'maximum_contents_characters':5000,'factual_correctness_separate_required':True,'unknown_keys_or_tools_allowed':False};(R/'STOP_AND_EXTENSION_POLICY.json').write_text(json.dumps(p,indent=2)+'\n')
manifest={'total':7720,'unchanged_teacher_actions':7640,'cleanup_unique_sources':4,'cleanup_copies':80,'cleanup_example_fraction':80/7720,'estimated_cleanup_token_fraction':.0472180109663,'all_action_content_hashes_preserved':{t.content_hash for t in tasks if t.input[-1].name=='submit_action'}=={json.loads(l)['content_hash'] for l in (A/'train-tasks.jsonl').open()},'prefix_balance':prefix,'source_action_sha256':hashlib.sha256((A/'train-tasks.jsonl').read_bytes()).hexdigest(),'source_cleanup_manifest_sha256':hashlib.sha256((C/'manifest.json').read_bytes()).hexdigest(),'selection_final_unchanged':True,'replacement_reason':'Observednativebase20incorrectcleanuptoolrouting;notidentitymigration','no_job_mutation':True}
assert manifest['all_action_content_hashes_preserved'];(R/'prepared.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
