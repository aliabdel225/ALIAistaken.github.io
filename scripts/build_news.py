#!/usr/bin/env python3
"""Build a source-linked daily news desk from publisher RSS feeds. No invented analysis."""
import datetime as dt, email.utils, html, json, re, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
SOURCES=[
 ("CISA Alerts","Advisories","https://www.cisa.gov/cybersecurity-advisories/all.xml"),
 ("BleepingComputer","Threats & Incidents","https://www.bleepingcomputer.com/feed/"),
 ("The Hacker News","Offensive & Vulnerabilities","https://feeds.feedburner.com/TheHackersNews"),
 ("SecurityWeek","Enterprise Security","https://www.securityweek.com/feed/"),
]
def clean(s):
 s=re.sub(r'<[^>]+>',' ',html.unescape(s or ''))
 return re.sub(r'\s+',' ',s).strip()
def tag_text(el,name):
 node=el.find(name)
 return ''.join(node.itertext()).strip() if node is not None else ''
def entries(label,category,url):
 req=urllib.request.Request(url,headers={'User-Agent':'CyberIntelligenceMagazine/1.0'})
 with urllib.request.urlopen(req,timeout=20) as resp:
  raw=resp.read(3_000_000)
 root=ET.fromstring(raw)
 items=root.findall('.//item')
 result=[]
 for item in items[:20]:
  title=clean(tag_text(item,'title')); link=tag_text(item,'link').strip()
  desc=clean(tag_text(item,'description'))[:450]
  date=tag_text(item,'pubDate')
  try: timestamp=email.utils.parsedate_to_datetime(date).astimezone(dt.timezone.utc)
  except Exception: timestamp=dt.datetime.now(dt.timezone.utc)
  if not title or not link.startswith('https://'):continue
  result.append(dict(title=title,url=link,summary=desc,source=label,category=category,date=timestamp.strftime('%b %d, %Y'),_timestamp=timestamp.isoformat()))
 return result
def main():
 stories=[]
 for label,cat,url in SOURCES:
  try: stories.extend(entries(label,cat,url))
  except Exception as exc: print('Feed unavailable:',label,exc)
 if not stories: raise SystemExit('No feeds reachable; preserving existing edition.')
 seen=set();unique=[]
 for s in sorted(stories,key=lambda a:a['_timestamp'],reverse=True):
  key=re.sub(r'[^a-z0-9]','',s['title'].lower())[:90]
  if key in seen:continue
  seen.add(key);unique.append(s)
 now=dt.datetime.now(dt.timezone.utc)
 recent=[s for s in unique if dt.datetime.fromisoformat(s['_timestamp'])>now-dt.timedelta(days=3)]
 selected=(recent or unique)[:18]
 for s in selected:s.pop('_timestamp',None)
 Path('news.json').write_text(json.dumps({'updated_at':now.isoformat(),'articles':selected},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Published',len(selected),'stories')
if __name__=='__main__':main()
