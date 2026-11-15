"""Freeze public Pete archive from actual linked Raw JSON URLs, with receipts."""
import concurrent.futures,hashlib,json,time
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse,parse_qs
ROOT=Path(__file__).resolve().parent
BASE='https://www.pokerbots.ac'
class Links(HTMLParser):
 def __init__(self,s):super().__init__();self.urls=[];self.feed(s)
 def handle_starttag(self,tag,attrs):
  if tag=='a' and (u:=dict(attrs).get('href')):self.urls.append(urljoin(BASE,u))
def fetch(u):
 for retry in range(4):
  try:return urlopen(Request(u,headers={'User-Agent':'pokerbots-training-archive/1.0'}),timeout=30).read()
  except Exception:
   if retry==3:raise
   time.sleep(2**retry)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 (ROOT/'raw').mkdir(exist_ok=True);(ROOT/'listings').mkdir(exist_ok=True)
 cutoff=datetime.now(timezone.utc);seen=set();found=set();listing=[]
 url=BASE+'/matches?entry=house-professor-pete'
 while url and url not in seen:
  seen.add(url);b=fetch(url);p=ROOT/'listings'/f'page-{len(seen)}.html';p.write_bytes(b)
  urls=Links(b.decode()).urls
  found.update(u for u in urls if '/matches/m_' in u)
  listing.append({'url':url,'file':str(p.relative_to(ROOT)),'sha256':sha(b),'matches':len(found)})
  nxt=[u for u in urls if urlparse(u).path=='/matches' and int(parse_qs(urlparse(u).query).get('page',['1'])[0])>len(seen)]
  url=nxt[0] if nxt else None
 print('Discovered',len(found),'Pete matches',flush=True)
 def one(u):
  ident=urlparse(u).path.rsplit('/',1)[1];row={'id':ident,'replay_url':u}
  try:
   links=Links(fetch(u).decode()).urls;raw=[v for v in links if urlparse(v).path.endswith('.json')]
   if len(raw)!=1:raise ValueError('Raw JSON link count')
   b=fetch(raw[0]);m=json.loads(b)
   if m['id']!=ident:raise ValueError('Raw ID mismatch')
   row.update(raw_url=raw[0],sha256=sha(b),fetched_at=datetime.now(timezone.utc).isoformat(),status=m.get('status'))
   if m.get('status')!='complete':row['result']='incomplete'
   elif datetime.fromisoformat(m['finished_at'])>cutoff:row['result']='after_cutoff'
   else:
    (ROOT/'raw'/f'{ident}.json').write_bytes(b);row['result']='complete'
  except Exception as e:row.update(result='failed',error=str(e))
  return row
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for row in pool.map(one,sorted(found)):
   rows.append(row);(ROOT/'manifest.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
   print(len(rows),row['id'],row['result'],flush=True)
 summary={'source':BASE+'/matches?entry=house-professor-pete','cutoff':cutoff.isoformat(),'discovered':len(found),'listing_pages':listing,'results':{k:sum(r['result']==k for r in rows) for k in ['complete','failed','incomplete','after_cutoff']}}
 (ROOT/'collection.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
