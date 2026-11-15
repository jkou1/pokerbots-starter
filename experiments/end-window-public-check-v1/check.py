"""One anonymous read of the miner's existing BASE/team URLs; no AC2 credentials."""
import asyncio,hashlib,json,re,time
from pathlib import Path
import httpx
R=Path(__file__).resolve().parent;miner=Path('/Users/lance/Documents/pokerbots-public-miner/experiments/public-failure-miner-v1/miner.py');arena=Path('/Users/lance/Documents/pokerbots-public-miner/vals_tools/arena.py');base=re.search(r'^BASE = "([^"]+)"',arena.read_text(),re.M)[1];org=re.search(r'^OUR_ORG = "([^"]+)"',miner.read_text(),re.M)[1];urls={'global_source_BASE':base,'current_team':base+'/teams/'+org};started=time.time()
async def main():
 async with httpx.AsyncClient(timeout=20,follow_redirects=True,trust_env=False)as client:
  async def get(label,url):
   try:
    response=await client.get(url);raw=response.content;(R/f'raw/{label}.body').write_bytes(raw);text=raw.decode('utf-8','replace');title=re.search(r'<title[^>]*>(.*?)</title>',text,re.S|re.I);quota=bool(re.search(r'quota|resource.{0,30}exceed|rate.limit|limit.exceed|payment.required',text,re.I));timestamps=re.findall(r'<time[^>]*datetime=[\"\x27]([^\"\x27]+)',text,re.I);updated=re.findall(r'.{0,60}(?:last updated|updated at|as of).{0,140}',text,re.I);return {'requested_url':url,'final_url':str(response.url),'status':response.status_code,'entity_bytes':len(raw),'body_sha256':hashlib.sha256(raw).hexdigest(),'title':title[1]if title else None,'upstream_quota_or_limit_text_present':quota,'explicit_time_elements':timestamps,'visible_update_text_candidates':updated[:5],'headers_not_evidence_of_leaderboard_freshness':{k:response.headers[k]for k in['date','age','last-modified','etag','cache-control','content-type']if k in response.headers},'leaderboard_current_rank':'UNKNOWN','source_freshness':'UNKNOWN unless an explicit leaderboard data-generation timestamp is independently grounded; HTTPDate/build/cache times do not establish it.','anonymous_no_AC2auth':True}
   except Exception as e:return {'requested_url':url,'error':type(e).__name__+':'+str(e),'leaderboard_current_rank':'UNKNOWN','source_freshness':'UNKNOWN','anonymous_no_AC2auth':True}
  data=dict(zip(urls,await asyncio.gather(*(get(k,v)for k,v in urls.items()))))
 receipt={'started_epoch':started,'completed_epoch':time.time(),'source_urls_exactly_from_existing_miner':True,'miner_source_sha256':hashlib.sha256(miner.read_bytes()).hexdigest(),'arena_source_sha256':hashlib.sha256(arena.read_bytes()).hexdigest(),'requests':data,'no_API_route_discovery_or_auth':True,'no_models_or_miner_restart_or_billing_changes':True,'conclusion':'Current public rank/freshness UNKNOWN; inspect source-specific evidence without treating HTTPDate as leaderboard timestamp.'};(R/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
asyncio.run(main())
