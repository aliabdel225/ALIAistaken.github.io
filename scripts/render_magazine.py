#!/usr/bin/env python3
"""Render a source-attributed editorial magazine from dated RSS evidence.

No AI service, invented quotations, speculative CVE details or copied full articles.
Each issue contains an executive briefing, categorized coverage, analyst checklists,
network/security context, an authorized lab and original publisher links.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(".")
ZONE = ZoneInfo("America/New_York")
TOPICS = {
 "vulnerability": ("Vulnerability Intelligence", "Identify affected assets, confirm vendor patches and prioritize internet-exposed systems. Correlate relevant application, process and network telemetry before treating exploitation as confirmed.", "Exposure validation"),
 "ransomware": ("Ransomware & Incident Response", "Review remote-access authentication, privileged changes, backup integrity and lateral movement telemetry. Preserve evidence and coordinate containment with service owners.", "Incident triage"),
 "network": ("Network Security", "Review management-plane access, segmentation, VPN authentication, firewall changes and east-west traffic. Verify exposure against the original advisory.", "Network exposure"),
 "offensive": ("Offensive Security Research", "Reproduce findings only in a controlled authorized lab. Distinguish scanner output, proof-of-concept execution and evidence of actual compromise.", "Authorized validation"),
 "threat": ("Threat Intelligence", "Map confirmed behaviors to ATT&CK techniques only when supported by evidence. Develop hypotheses around identity misuse, persistence and command-and-control activity.", "Threat hunting"),
 "general": ("Security Operations", "Assess affected technologies, evidence quality and response priorities. Avoid assuming that a headline alone proves compromise.", "Security assessment"),
}
def esc(v):
 return html.escape(str(v or ""),quote=True)
def topic(a):
 t=(a.get("title","")+" "+a.get("category","")).lower()
 if any(x in t for x in ("cve-","vulnerab","patch","zero-day","exploit")): return "vulnerability"
 if any(x in t for x in ("ransom","hospital","breach","incident")): return "ransomware"
 if any(x in t for x in ("vpn","router","firewall","network","switch","sd-wan")): return "network"
 if any(x in t for x in ("pentest","red team","offensive","researcher")): return "offensive"
 if any(x in t for x in ("threat","malware","actor","campaign")): return "threat"
 return "general"
CSS="""
:root{color-scheme:dark;--red:#fa5158}*{box-sizing:border-box}
body{background:#090a0c;color:#f4f4f4;margin:0;font:16px/1.8 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:#ff777d}header,main,footer{max-width:1060px;margin:auto;padding:26px}
header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #383838}
header a{text-decoration:none}header strong{letter-spacing:.1em}
h1{font-size:clamp(2.8rem,8vw,6.2rem);letter-spacing:-.065em;line-height:1.03;margin:18px 0 26px}
h2{font-size:clamp(1.65rem,4vw,2.55rem);line-height:1.22;margin:12px 0 22px}
h3{font-size:1.18rem;margin:26px 0 8px}p,li{color:#ccc}
.kicker{color:var(--red);text-transform:uppercase;letter-spacing:.15em;font-size:.8rem;font-weight:800}
.hero{padding:70px 0 50px;border-bottom:1px solid #343434}
.deck{font-size:1.22rem;max-width:790px}.meta{color:#999;font-size:.9rem}
.section{padding:54px 0;border-bottom:1px solid #343434}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.card{background:#17191c;border:1px solid #353535;border-radius:14px;padding:24px}
.card h3{margin:8px 0}.feature{background:linear-gradient(130deg,#241316,#161719);padding:30px;border-radius:16px;border:1px solid #423034}
.callout{background:#191b1e;border-left:4px solid var(--red);padding:20px 24px;margin:25px 0}
table{width:100%;border-collapse:collapse}td,th{padding:12px;text-align:left;border-bottom:1px solid #393939;vertical-align:top}
th{color:#ff8388}footer{color:#888;padding-bottom:48px}
@media(max-width:650px){.grid{grid-template-columns:1fr}.hero{padding-top:40px}header{flex-wrap:wrap}.feature{padding:20px}}
"""
def main():
 now=dt.datetime.now(ZONE)
 date=now.date().isoformat()
 source=json.loads((ROOT/"news.json").read_text(encoding="utf-8"))
 articles=source.get("articles",[])
 if len(articles)<3: raise SystemExit("Not enough source-linked stories; preserve existing editions.")
 # Never silently replace a human-edited issue.
 dest=ROOT/("news-"+date+".html")
 if dest.exists():
  print("Existing issue preserved:",dest)
  return
 unique=[];seen=set()
 for a in articles:
  url=a.get("url","")
  if not url.startswith("https://") or not a.get("title") or not a.get("source"):continue
  if url in seen:continue
  seen.add(url);unique.append(a)
 if len(unique)<3: raise SystemExit("Too few usable cited stories.")
 day=now.strftime("%A, %B %-d, %Y")
 body=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',f'<title>{esc(day)} | The Security Intelligence Magazine</title>',f'<style>{CSS}</style></head><body><header><a href="index.html"><strong>ALI ABDELGHANI</strong></a><a href="news.html">← All Editions</a></header><main>']
 body += ['<section class="hero"><div class="kicker">Daily Cybersecurity Intelligence · Morning Edition</div><h1>THE SECURITY<br>INTELLIGENCE<br>MAGAZINE<span style="color:var(--red)">.</span></h1>',f'<div class="meta">{esc(day.upper())} · {len(unique)} SOURCE-LINKED STORIES</div>','<p class="deck">Cybersecurity reporting with technical context, analyst priorities, original sources and practical defensive takeaways.</p></section>']
 body += ['<section class="section"><div class="kicker">The Front Page</div><h2>Today’s Intelligence Briefing</h2><p>Today’s edition surveys recently published cybersecurity reporting. Headlines and excerpts are attributed to their original publishers; the defensive guidance below is general analytical context, not a claim that a specific attack step occurred.</p><div class="grid">']
 for a in unique[:4]:
  body.append(f'<div class="card"><div class="kicker">{esc(topic(a).replace("_"," "))}</div><h3>{esc(a["title"])}</h3><p>{esc(a.get("summary",""))}</p></div>')
 body.append('</div></section>')
 body += ['<section class="section"><div class="kicker">The Threat Dashboard</div><h2>Coverage at a Glance</h2><table><thead><tr><th>Focus</th><th>Source story</th></tr></thead><tbody>']
 for a in unique[:10]:
  body.append(f'<tr><td>{esc(TOPICS[topic(a)][0])}</td><td>{esc(a["title"])}</td></tr>')
 body.append('</tbody></table></section>')
 for n,a in enumerate(unique,1):
  cat,advice,practice=TOPICS[topic(a)]
  body += [f'<section class="section"><div class="kicker">Feature {n:02d} · {esc(cat)}</div><h2>{esc(a["title"])}</h2>',f'<div class="meta">Source: {esc(a["source"])} · Published: {esc(a.get("date","Date not provided"))}</div>',f'<div class="feature"><h3>What is being reported?</h3><p>{esc(a.get("summary") or "See the original report for the available details.")}</p></div>','<h3>Why security teams should care</h3>',f'<p>{esc(advice)}</p>','<h3>Investigation and validation</h3>',f'<p>Start with asset inventory, the original publisher’s evidence and the relevant vendor advisory. Validate scope before taking disruptive action. Record what is confirmed, what is inferred and what remains unknown. The source excerpt alone may not contain enough information to establish the complete attack chain.</p>',f'<div class="callout"><strong>Analyst takeaway:</strong> {esc(practice)} — document evidence, exposure and practical remediation before drawing conclusions.</div>',f'<a href="{esc(a["url"])}" target="_blank" rel="noopener noreferrer">Read the original report — {esc(a["source"])} ↗</a>','</section>']
 body += ['<section class="section"><div class="kicker">SOC &amp; Network Defense</div><h2>Detection Engineering Priorities</h2><p>Correlate identity events, unexpected privilege changes, unusual process execution, external connections and network-management modifications. Baseline expected activity and test detections against known-good administrative behavior to reduce false positives.</p><table><tr><th>Telemetry</th><th>Questions to ask</th></tr><tr><td>Authentication</td><td>Were there unusual sources, times, accounts or new sessions?</td></tr><tr><td>Network traffic</td><td>Were there unexpected destinations, ports or lateral connections?</td></tr><tr><td>Endpoint activity</td><td>Did processes, persistence mechanisms or privileges change?</td></tr><tr><td>Infrastructure</td><td>Were firewall, VPN, identity or management configurations altered?</td></tr></table></section>','<section class="section"><div class="kicker">Hands-On Lab · Authorized Systems Only</div><h2>Build a News-to-Detection Investigation</h2><p><strong>Difficulty:</strong> Intermediate · <strong>Duration:</strong> 45–60 minutes</p><p>Choose one report from today’s issue. In a dedicated lab, identify its affected technology or a comparable benign event. Write an investigation hypothesis, identify relevant log sources and build a detection query or packet-analysis filter. Test against permitted sample activity and record the limitations of your findings.</p><p><strong>Deliverable:</strong> A one-page SOC report containing the hypothesis, evidence, observations, false-positive considerations, recommended controls and a direct citation to the original source.</p></section>','<section class="section"><div class="kicker">The Editor’s Desk</div><h2>Today’s Priorities</h2><p>Prioritize confirmed active exploitation, externally reachable assets, privileged management interfaces and incidents affecting critical services. Use vendor advisories and original reporting to confirm technical specifics and remediation steps.</p><div class="callout"><strong>Sources &amp; attribution.</strong> Each feature names its original publisher and links to its report. Publication dates reflect feed metadata. Summaries and analyst context are not substitutes for full source verification.</div></section>','<p style="padding:35px 0"><a href="news.html">← Browse all published editions</a></p></main><footer>© 2026 Ali Abdelghani · The Security Intelligence Magazine</footer></body></html>']
 dest.write_text("".join(body),encoding="utf-8")
 manifest=ROOT/"news-archive.json"
 try: index=json.loads(manifest.read_text(encoding="utf-8"))
 except (FileNotFoundError,json.JSONDecodeError):index={"issues":[]}
 index["issues"]=[i for i in index.get("issues",[]) if i.get("date")!=date]
 index["issues"].append({"date":date,"title":day+" — The Security Intelligence Magazine","summary":"Full morning edition: security briefings, technical context, analyst guidance and original reporting.","count":len(unique)})
 index["issues"].sort(key=lambda x:x["date"],reverse=True)
 manifest.write_text(json.dumps(index,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Published full magazine",dest)
if __name__=="__main__":main()
