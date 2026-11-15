"""CPU-only predetermined checkpoints; all facts from cleanup INPUT, never raw engine state."""
import json,gzip,hashlib,re,sys,collections,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'cleanup-multihand-rl20-v1'));from factual_filter import visible_fact_ledger,validate_contents,PATTERN
sys.path.insert(0,'/Users/lance/Documents/pokerbots-overnight-eval');from vals_tools.cleanup_score import cleanup_protocol
R=Path(__file__).resolve().parent;E=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/base20-development-v1');H=[5,10,20,25,30];records=[];sources=[]
def digest(x):return hashlib.sha256(x).hexdigest()
def score(tag,game,n,note,prompt,ledger,source,protocol,scope):
 facts=validate_contents(note,ledger,n)if isinstance(note,str)and note else{'accepted':False,'errors':['no nonempty proposed output'],'claims':0,'claimed_hand_numbers':[]};prior=[h for h in facts.get('claimed_hand_numbers',[])if h<n and h in ledger];blocks=[{'claimed_hand':int(m[1]),'temporal_scope':'current'if int(m[1])==n else'prior'if int(m[1])<n else'future','check':validate_contents(m.group(0),ledger,int(m[1]))}for m in PATTERN.finditer(note or'')];records.append({'model':tag,'game_group':game,'hand':n,'source_sha256':source,'cleanup_input_sha256':digest(prompt.encode()),'proposed_note_sha256':digest((note or'').encode()),'proposed_note_characters':len(note or''),'format':protocol,'fact_checker':facts,'parsed_blocks':blocks,'useful_verified_prior_fact_blocks':len(prior)if facts.get('accepted')else 0,'current_block_fully_verified':bool(facts.get('accepted')),'unknown_scope':'Residual/free prose is unverified, not automatically false. Prior scratchpad text is never a ground-truth ledger.','input_scope':scope})
summary=json.loads((E/'summary.json').read_text())
for tag in ['incumbent','rl20']:
 for src in summary['runs'][tag]['source_manifest']:
  p=E/tag/'raw'/Path(src['source']).name;raw=p.read_bytes();assert digest(raw)==src['raw_sha256'];d=json.loads(raw);private=d['private'];seat=next(x['seat']for x in summary['runs'][tag]['games']if x['seed']==src['seed']);hands=private[seat]['hands'];spans=[{'input':json.dumps([{'type':'message','role':'user','content':x.get('cleanup',{}).get('prompt','')}])}for x in hands.values()];ledger=visible_fact_ledger(spans);sources.append({'model':tag,'game_group':str(src['seed']),'source_sha256':digest(raw),'policy_seat':seat,'visible_cleanup_ledger_hands':len(ledger)})
  for n in H:
   if str(n)not in hands or not hands[str(n)].get('cleanup'):continue
   c=hands[str(n)]['cleanup'];calls=(c.get('attempts')or[{}])[-1].get('update_calls')or[];note=None
   if len(calls)==1:
    try:note=(json.loads(calls[0])if isinstance(calls[0],str)else calls[0]).get('contents')
    except (ValueError,TypeError):pass
   score(tag,str(src['seed']),n,note,c['prompt'],ledger,digest(raw),cleanup_protocol([c]),'Actual recorded cleanup.prompt only; earlier cleanup prompts establish prior facts. Full raw engine state/cards never consulted.')
progress=json.loads(Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/base-grpo5-development-v1/progress.json').read_text());allowed=set(progress.get('policy_game_progress',{}))|set(progress.get('completed_agent_trace_ids',[]));spans=[json.loads(l)for l in gzip.open(R/'raw/parent5-visible-spans.jsonl.gz','rt')];grouped=collections.defaultdict(list)
for s in spans:
 if s['trace_id']not in allowed:raise ValueError('Unattributed nonpolicy trace: quarantine rather than mixing seats')
 grouped[s['trace_id']].append(s)
for trace,group in grouped.items():
 ledger=visible_fact_ledger(group);sources.append({'model':'parent5','game_group':trace,'visible_cleanup_ledger_hands':len(ledger)})
 for s in group:
  p=json.loads(s['input']);last=next((x.get('content','')for x in reversed(p)if x.get('role')=='user'),'');m=re.match(r'^## Hand (\d+) is over',last)
  if not m or int(m[1])not in H:continue
  n=int(m[1]);out=json.loads(s['output']);calls=[x for x in out if x.get('type')=='function_call'];args={}
  if len(calls)==1:
   try:args=json.loads(calls[0]['arguments'])
   except (ValueError,TypeError):pass
  note=args.get('contents');protocol={'emitted_exact_one_contents_only_update':len(calls)==1 and calls[0].get('name')=='update_scratchpad'and set(args)=={'contents'}and isinstance(note,str)and len(note)<=5000,'host_acceptance_pending':True}
  score('parent5',trace,n,note,last,ledger,digest((s['input']+'\n'+s['output']).encode()),protocol,'Exact native policy P/R, including original assistant/tool history. Ledger uses original cleanup USER observations, never incoming scratchpad as truth.')
  (R/f'raw/evidence-{trace}-{n}.json').write_text(json.dumps({'span_id':s['span_id'],'input':p,'output':out},indent=2)+'\n')
out={'at_epoch':time.time(),'predetermined_hands':H,'models':{},'sources':sources,'records':records,'no_model_calls':True,'no_FINAL_read':True,'strict_checker_scope':'Only full hand N: board ...; stacks {...} blocks are accepted. Free prose is UNKNOWN unless separately verified; zero checker acceptance is not a claim every note is false.','comparison_scope':'Cached C/RL20 same development seed set, different decisions/outcomes; parent5 incomplete so counts are not equal-exposure memory-quality ranking.'}
for tag in ['parent5','incumbent','rl20']:
 xs=[x for x in records if x['model']==tag];out['models'][tag]={'planned_checkpoints':20,'available':len(xs),'pending_or_absent':20-len(xs),'missing_scope':'pending parent games/hand milestones'if tag=='parent5'else'complete cachedgames: policy had no cleanup at these milestones, including busts; not pending','strict_fully_verified_notes':sum(x['fact_checker'].get('accepted',False)for x in xs),'notes_with_unknown_residual_prose':sum(any('unparsed' in e or 'no fully recognized' in e for e in x['fact_checker'].get('errors',[]))for x in xs),'strict_unknown_or_rejected':sum(not x['fact_checker'].get('accepted',False)for x in xs),'notes_with_parsed_board_or_stack_contradiction':sum(any('differs' in e for e in x['fact_checker'].get('errors',[]))for x in xs),'contradicted_current_blocks':sum(b['temporal_scope']=='current'and any('differs'in e for e in b['check'].get('errors',[]))for x in xs for b in x['parsed_blocks']),'contradicted_prior_blocks':sum(b['temporal_scope']=='prior'and any('differs'in e for e in b['check'].get('errors',[]))for x in xs for b in x['parsed_blocks']),'verified_useful_prior_blocks':sum(x['useful_verified_prior_fact_blocks']for x in xs),'format_emitted_exact_or_host_final_accepted':sum(x['format'].get('emitted_exact_one_contents_only_update',False)or x['format'].get('exact_valid_final_updates',0)>0 for x in xs)}
(R/'snapshot.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['models'],indent=2))
