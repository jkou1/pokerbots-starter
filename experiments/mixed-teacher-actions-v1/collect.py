"""Freeze both teachers' own public matches, reusing proven exact-byte caches."""
import concurrent.futures,hashlib,json,re,time
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse,parse_qs
ROOT=Path(__file__).resolve().parent;BASE='https://www.pokerbots.ac'
TEACHERS={'house-professor-pete':'Professor Pete','house-chatty-carlos':'Chatty Carlos'}
CACHE=ROOT.parent/'pete-postflop-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
class Links(HTMLParser):
 def __init__(self,text):super().__init__();self.urls=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  if tag=='a' and (u:=dict(attrs).get('href')):self.urls.append(urljoin(BASE,u))
def fetch(url):
 for retry in range(4):
  try:return urlopen(Request(url,headers={'User-Agent':'pokerbots-mixed-teacher-archive/1.0'}),timeout=30).read()
  except Exception:
   if retry==3:raise
   time.sleep(2**retry)
def main():
 (ROOT/'raw').mkdir(exist_ok=True);(ROOT/'listings').mkdir(exist_ok=True)
 cutoff=datetime.fromisoformat(json.loads((ROOT/'collection.json').read_text())['cutoff']) if (ROOT/'collection.json').exists() else datetime.now(timezone.utc)
 cache={};proof={}
 if (ROOT/'manifest.jsonl').exists():
  for line in (ROOT/'manifest.jsonl').open():
   prior=json.loads(line);path=ROOT/'raw'/f'{prior["id"]}.json'
   if prior.get('result')=='complete' and path.exists() and sha(path.read_bytes())==prior['sha256']:
    cache[prior['id']]={**prior,'source_bytes_path':str(path)}
 for line in (CACHE/'manifest.jsonl').open():
  r=json.loads(line);p=CACHE/'raw'/f'{r["id"]}.json'
  if p.exists() and sha(p.read_bytes())==r['sha256']:
   cache[r['id']]={**r,'source_bytes_path':str(p)}
   m=json.loads(p.read_bytes())
   for s in m['seats']:
    e=s['entry']
    if e['id'] in TEACHERS and e['id'] not in proof:proof[e['id']]={'entry':e,'match_id':m['id'],'raw_url':r['raw_url'],'sha256':r['sha256']}
 assert set(proof)==set(TEACHERS),'Canonical IDs must be observed in actual raw seat maps'
 (ROOT/'canonical-teachers.json').write_text(json.dumps(proof,indent=2)+'\n')
 for folder in ['arena-incumbent-audit','arena-leader-audit']:
  manifest=Path('/Users/lance/Documents/pokerbots-overnight-eval/data/experiments')/folder/'manifest.jsonl'
  if manifest.exists():
   for line in manifest.open():
    r=json.loads(line);p=Path(r['source_bytes_path'])
    if p.exists() and sha(p.read_bytes())==r['sha256']:cache[r['id']]=r
 found={};listings=[]
 for teacher in TEACHERS:
  url=BASE+'/matches?entry='+teacher;seen=set()
  while url and url not in seen:
   seen.add(url);b=fetch(url);p=ROOT/'listings'/f'{teacher}-page-{len(seen)}.html';p.write_bytes(b);urls=Links(b.decode()).urls
   matches=[u for u in urls if re.fullmatch(r'/matches/m_[A-Za-z0-9_]+',urlparse(u).path)]
   for u in matches:found.setdefault(u,set()).add(teacher)
   listings.append({'teacher':teacher,'url':url,'file':str(p.relative_to(ROOT)),'sha256':sha(b),'match_links':len(matches)})
   nxt=[u for u in urls if urlparse(u).path=='/matches' and parse_qs(urlparse(u).query).get('entry')==[teacher] and int(parse_qs(urlparse(u).query).get('page',['1'])[0])>len(seen)]
   url=nxt[0] if nxt else None
 print('Discovered',len(found),'unique matches across both canonical teachers',flush=True)
 def one(url):
  ident=urlparse(url).path.rsplit('/',1)[1];r={'id':ident,'replay_url':url,'listed_for_teachers':sorted(found[url])}
  try:
   old=cache.get(ident)
   if old:
    b=Path(old['source_bytes_path']).read_bytes();raw_url=old['raw_url'];r.update(cache_reused=True,cache_source=old['source_bytes_path'],original_fetched_at=old.get('fetched_at'),original_url_verified_at=old.get('url_verified_at'))
   else:
    links=Links(fetch(url).decode()).urls;raw=[u for u in links if urlparse(u).path.endswith('.json')]
    if len(raw)!=1:raise ValueError('Expected exactly one actual RawJSON link')
    raw_url=raw[0];b=fetch(raw_url);r['cache_reused']=False
   m=json.loads(b)
   if m['id']!=ident or m.get('schema')!='vals-arena.match/1':raise ValueError('Raw match identity/schema mismatch')
   r.update(raw_url=raw_url,sha256=sha(b),status=m.get('status'),fetched_or_reused_at=datetime.now(timezone.utc).isoformat(),finished_at=m.get('finished_at'))
   if m.get('status')!='complete':r['result']='incomplete'
   elif datetime.fromisoformat(m['finished_at'])>cutoff:r['result']='after_cutoff'
   else:(ROOT/'raw'/f'{ident}.json').write_bytes(b);r['result']='complete'
  except Exception as e:r.update(result='failed',error=f'{type(e).__name__}: {e}')
  return r
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for r in pool.map(one,sorted(found)):
   rows.append(r);(ROOT/'manifest.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows))
   if len(rows)%20==0 or r['result']!='complete':print(len(rows),r['id'],r['result'],flush=True)
 result={'cutoff':cutoff.isoformat(),'teachers':TEACHERS,'discovered_unique_matches':len(found),'listings':listings,'results':{k:sum(r['result']==k for r in rows) for k in ['complete','failed','incomplete','after_cutoff']},'cache_reused':sum(bool(r.get('cache_reused')) for r in rows)}
 (ROOT/'collection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='listings'},indent=2))
if __name__=='__main__':main()
