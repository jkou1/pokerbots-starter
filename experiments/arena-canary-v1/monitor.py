"""Inactive until explicit confirmed activation; actual Arena spans, read-only."""
import collections,hashlib,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
from parser import analyze,decoded
sys.path.insert(0,'/tmp');from pokerbots_working_client import working_client,preflight_identity
from ac2.sdk.analytics.types import QuerySpec,ColumnSpec,FieldFilter
R=Path(__file__).resolve().parent;CONFIG=R/'activation.json';STATUS=Path('/tmp/pokerbots-arena-canary-status.json');ALERTS=Path('/tmp/pokerbots-arena-canary-alerts.json');E=R/'evidence';os.umask(0o077);E.mkdir(exist_ok=True);E.chmod(0o700)
statefile=E/'state.json';saved=json.loads(statefile.read_text()) if statefile.exists() else {'versions':{}};c=None
utc=lambda:datetime.now(timezone.utc)
def atomic(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,default=str)+'\n');tmp.chmod(0o600);tmp.replace(path)
def timestamp(value):
 d=datetime.fromisoformat(str(value).replace('Z','+00:00'));return (d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d).astimezone(timezone.utc)
while utc()<datetime.fromisoformat('2026-11-15T17:00:00+00:00'):
 delay=45;status={'updated_at':utc().isoformat(),'monitor_pid':os.getpid(),'activation_path':str(CONFIG),'mode':'inactive','read_only':True,'automatic_rollback':False,'alerts':[]}
 try:
  cfg=json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
  if cfg.get('active') and cfg.get('promotion_confirmed'):
   assert cfg.get('model') and cfg.get('inference_id','').startswith('infer_') and cfg.get('version') is not None
   cutoff=timestamp(cfg['cutover_utc']);assert cutoff<=utc();delay=max(30,min(60,int(cfg.get('poll_seconds',45))))
   fingerprint=hashlib.sha256(json.dumps({k:cfg[k] for k in ['model','inference_id','version','cutover_utc']},sort_keys=True).encode()).hexdigest()[:16]
   group=saved['versions'].setdefault(fingerprint,{'pin':{k:cfg[k] for k in ['model','inference_id','version','cutover_utc']},'records':{},'polls':0,'observed_queries':0})
   if c is None:c=working_client();identity=preflight_identity(c)
   columns=['start_time','end_time','job_id','trace_id','span_id','name','attributes','input','output','status','error_message']
   result=c.analytics.query(spec=QuerySpec(source='spans',projects=['vals-hackathon'],job_ids=[cfg['inference_id']],columns=[ColumnSpec(field=f) for f in columns],filters=[FieldFilter(field='name',op='eq',value='inference.request')],limit=200,sort_by='start_time',sort_order='desc'))
   group['polls']+=1;group['observed_queries']+=len(result.rows);skipped=collections.Counter();seen_before=set(group['records'])
   for row in sorted(result.rows,key=lambda x:str(x.get('start_time',''))):
    attrs=decoded(row.get('attributes') or {});span=str(row.get('span_id',''))
    if not span:skipped['no_span_id']+=1;continue
    if span in group['records']:continue
    if not str(attrs.get('conversation_id','')).startswith('vals-arena/'):skipped['not_actual_arena']+=1;continue
    if str(attrs.get('inference_version'))!=str(cfg['version']):skipped['other_version']+=1;continue
    if attrs.get('inference_deployment_id',row.get('job_id'))!=cfg['inference_id']:skipped['other_inference_id']+=1;continue
    if timestamp(row['start_time'])<cutoff:skipped['before_cutover']+=1;continue
    if not row.get('end_time') and not row.get('error_message') and str(row.get('status','')).lower() not in ['error','failed']:skipped['incomplete']+=1;continue
    parsed=analyze(row)
    if parsed is None:skipped['unknown_conversation_format']+=1;continue
    filename='span-'+hashlib.sha256(span.encode()).hexdigest()+'.json';atomic(E/filename,row);parsed['evidence_path']=str(E/filename);group['records'][span]=parsed
   records=sorted(group['records'].values(),key=lambda x:str(x['start_time']));logical={}
   for r in records:
    key=r['logical_turn_id']
    if key not in logical:logical[key]={**r,'attempts':0,'failed_attempts':0}
    logical[key]['attempts']+=1;logical[key]['failed_attempts']+=not r['valid_protocol'];logical[key]['valid_protocol']=logical[key]['failed_attempts']==0
   unique=list(logical.values());decisions=[r for r in unique if r['kind']=='decision'];cleanup=[r for r in unique if r['kind']=='cleanup'];first40=decisions[:40];alerts=[]
   for r in records:
    for critical in r['critical']:alerts.append({'kind':'critical_output','reason':critical,'span_id':r['span_id'],'match_id':r['match_id'],'evidence_path':r['evidence_path']})
   bad40=sum(not r['valid_protocol'] for r in first40)
   if len(first40)==40 and bad40/40>=.05:alerts.append({'kind':'first40_invalid_rate','invalid':bad40,'decisions':40,'rate':bad40/40})
   enum=[r for r in decisions if 'invalid_action_enum' in r['errors']];badcleanup=[r for r in cleanup if not r['valid_protocol']]
   if len(enum)>=2:alerts.append({'kind':'repeated_enum_failures','count':len(enum)})
   if len(badcleanup)>=2:alerts.append({'kind':'repeated_cleanup_failures','count':len(badcleanup)})
   matches={}
   for match in sorted({r['match_id'] for r in records}):
    rs=[r for r in unique if r['match_id']==match];ds=[r for r in rs if r['kind']=='decision'];cs=[r for r in rs if r['kind']=='cleanup'];matches[match]={'decisions':len(ds),'invalid_decisions':sum(not r['valid_protocol'] for r in ds),'cleanup':len(cs),'invalid_cleanup':sum(not r['valid_protocol'] for r in cs)}
   status.update(mode='active',activation_fingerprint=fingerprint,pin=group['pin'],identity=identity,observed_attempt_spans=len(records),logical_turn_dedup='Conversation+decisionvisibleobservationhash;cleanupconversation. Any failed attempt marks unique turn invalid; span attempts reported separately.',decisions=len(decisions),invalid_decisions=sum(not r['valid_protocol'] for r in decisions),cleanup=len(cleanup),invalid_cleanup=len(badcleanup),first40_observed=len(first40),first40_invalid=bad40,per_match=matches,errors=dict(collections.Counter(e for r in records for e in r['errors'])),alerts=alerts,last_query_skipped=dict(skipped),legal_text_unsupported=sum(not r['legal_text_supported'] for r in decisions),unsupported=['No offered tool definitions: optional p_win/read requirements unsupported','Cleanup protocol checks do not establish factual correctness','Lexical own-say flags are bounded, not comprehensive moderation','Most recent200 span window; any coverage gaps are reported, not silently treated as zero failures'])
   if len(result.rows)==200 and result.rows and timestamp(result.rows[-1]['start_time'])>cutoff and not any(str(row.get('span_id','')) in seen_before for row in result.rows[-10:]):status['alerts'].append({'kind':'query_coverage_warning','reason':'Recent200window may omit older unseen spans'})
   atomic(statefile,saved)
  atomic(STATUS,status);atomic(ALERTS,{'updated_at':status['updated_at'],'mode':status['mode'],'alerts':status['alerts']})
 except Exception as exc:
  status.update(mode='error',error=f'{type(exc).__name__}: {str(exc)[:300]}');atomic(STATUS,status)
 print(status['updated_at'],status['mode'],'decisions',status.get('decisions',0),'alerts',len(status['alerts']),flush=True);time.sleep(delay)
atomic(STATUS,{'updated_at':utc().isoformat(),'mode':'stopped_at_deadline','monitor_pid':os.getpid(),'read_only':True,'automatic_rollback':False})
