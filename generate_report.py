#!/usr/bin/env python3
"""Blogger Prediction Aggregator — 2026 World Cup — Clean Light Edition"""

import json, os, re, sys, hashlib, urllib.request, io
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent.resolve()
DD, IDIR, OD = BASE/"data", BASE/"images", BASE/"output"
HTML = OD/"blogger_report.html"
for d in [DD, IDIR, OD]: d.mkdir(parents=True, exist_ok=True)

def dl(url, force=False):
    if not url: return ""
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    ext = ".png" if url.lower().endswith(".png") else ".jpg"
    lp = IDIR/f"{h}{ext}"
    if lp.exists() and not force: return f"../images/{h}{ext}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r: lp.write_bytes(r.read())
        return f"../images/{h}{ext}"
    except: return url

def parse_html(h):
    if not h: return {"raw":"","matches":[]}
    t = re.sub(r'<br\s*/?>','\n',h)
    for tag in ['p','span','/p','/span']: t = re.sub(rf'<{tag}[^>]*>','',t)
    t = re.sub(r'<[^>]+>','',t).strip()
    ms = []
    for part in [p.strip() for p in re.split(r'(?=世界杯)',t) if p.strip()]:
        m = {"raw":part,"teams":"","direction":"","index_rec":"","score_rec":"","total_goals":""}
        for line in [l.strip() for l in part.split('\n') if l.strip()]:
            for kw,k in [('方向','direction'),('竞猜方向','direction'),('竞足方向','direction'),
                         ('指数推荐','index_rec'),('指数','index_rec'),('比分','score_rec'),
                         ('灯牌','score_rec'),('娱乐','score_rec'),('格局','total_goals'),('解析','direction')]:
                if kw in line:
                    v = re.sub(r'.*[:：]','',line).strip()
                    if k=='direction' and m['direction']: continue
                    m[k] = v
        if ls := [l.strip() for l in part.split('\n') if l.strip()]:
            if tm := re.search(r'(.+?)[Vv][Ss]\.?(.+)', ls[0]):
                m["teams"] = f"{tm.group(1).strip()} vs {tm.group(2).strip()}"
        ms.append(m)
    return {"raw":t,"matches":ms}

def ext_title(title):
    i = {"match_num":"","home_team":"","away_team":"","kickoff_time":"","is_world_cup":"世界杯" in title}
    if nm := re.search(r'(\d{3})\s*(世界杯|场)?',title): i["match_num"]=nm.group(1)
    # Find ALL team pairs, use the LAST one (most reliable — team names tend to be at the end)
    tms = re.findall(r'([一-龥]{2,})\s*(?:[Vv][Ss]\.?|[～~—])\s*([一-龥]{2,})',title)
    if tms:
        # Prefer pairs that look like real team names (not generic words)
        real_teams = [(h,a) for h,a in tms if h not in ('世界杯','再度出击','出击') and a not in ('世界杯','再度出击','出击')]
        if real_teams: i["home_team"],i["away_team"] = real_teams[-1]
        else: i["home_team"],i["away_team"] = tms[-1]
        # Strip "世界杯" prefix from team names
        for k in ('home_team','away_team'):
            i[k] = re.sub(r'^世界杯','',i[k])
    if km := re.search(r'(\d{1,2}:\d{2})',title): i["kickoff_time"]=km.group(1)
    return i

def proc(entry):
    r = {"id":entry.get("id"),"au":entry.get("author",{}).get("nickname","?"),
         "av":entry.get("author",{}).get("avatar",""),"title":entry.get("title",""),
         "d":entry.get("create_date",""),"tm":entry.get("create_time_formatted",""),
         "bn":entry.get("buy_num",0),"rn":entry.get("read_num",0),
         "tg":[],"mh":"","ma":"","mn":"","mt":"","pr":{},"il":"","hi":False,"ht":False}
    for tg in entry.get("tags",{}).values():
        if isinstance(tg,list):
            for t in tg:
                if isinstance(t,dict) and t.get("name"): r["tg"].append(t["name"])
    mi = ext_title(entry.get("title",""))
    r["mh"]=mi["home_team"]; r["ma"]=mi["away_team"]; r["mn"]=mi["match_num"]; r["mt"]=mi["kickoff_time"]
    if iu := entry.get("img",""): r["il"]=dl(iu); r["hi"]=True
    if ch := entry.get("content",""): r["pr"]=parse_html(ch); r["ht"]=True
    return r

def load_all():
    es = []
    for jf in sorted(DD.glob("*.json")):
        try:
            for it in json.loads(jf.read_text(encoding="utf-8")).get("data",{}).get("list",[]):
                es.append(proc(it))
        except Exception as e: print(f"  WARN {jf.name}: {e}")
    return es

def merge_json(jp):
    data = json.loads(Path(jp).read_text(encoding="utf-8"))
    its = data.get("data",{}).get("list",[])
    if not its: print("WARN: no data"); return None
    ds = its[0].get("create_date",datetime.now().strftime("%Y-%m-%d"))
    dest = DD/f"{ds}.json"
    if dest.exists():
        ex = json.loads(dest.read_text(encoding="utf-8"))
        eids = {e["id"] for e in ex.get("data",{}).get("list",[])}
        new = [e for e in its if e["id"] not in eids]
        if new:
            ex["data"]["list"]=ex["data"]["list"]+new; ex["data"]["count"]=len(ex["data"]["list"])
            dest.write_text(json.dumps(ex,ensure_ascii=False,indent=2),encoding="utf-8")
            print(f"  merged {len(new)} into {ds}.json")
        else: print(f"  {ds}.json up to date")
    else:
        dest.write_text(Path(jp).read_text(encoding="utf-8"))
        print(f"  saved {ds}.json ({len(its)} entries)")
    return ds

# ============================================================
# Clean, readable, info-dense design. No dark mode.
# ============================================================
HTML_T = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>World Cup 2026 — Predictions</title>
<style>
:root{
    --bg: #f2f4f0;
    --card: #ffffff;
    --border: #e0e3dd;
    --border-hover: #c0c8b8;
    --green: #1a6e3e;
    --green-bg: #e8f5eb;
    --gold: #b8860b;
    --gold-bg: #fef6e8;
    --text: #1a1c18;
    --text-2: #5a5d56;
    --text-3: #90938c;
    --radius: 8px;
    --font: "Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
    --font-mono: "Cascadia Code","Fira Code","Consolas",monospace;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh;-webkit-font-smoothing:antialiased;line-height:1.5}

/* Header */
.header{background:var(--green);color:#fff;text-align:center;padding:24px 20px 20px}
.header h1{font-size:1.25rem;font-weight:700;letter-spacing:1px}
.header .sub{font-size:0.72rem;opacity:0.8;letter-spacing:3px;margin-top:2px}

/* Filter bar */
.bar{display:flex;justify-content:center;align-items:center;gap:12px;padding:12px 20px;position:sticky;top:0;z-index:40;background:rgba(255,255,255,0.94);border-bottom:1px solid var(--border);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.bar label{font-size:0.8rem;font-weight:600;color:var(--text-2)}
.bar select{padding:7px 30px 7px 12px;border-radius:6px;border:1px solid var(--border);background:#fff;color:var(--text);font-size:0.82rem;font-weight:550;cursor:pointer;outline:none;min-width:160px;appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 8px center}
.bar select:focus{border-color:var(--green)}
.bar .badge{background:var(--green);color:#fff;padding:4px 14px;border-radius:14px;font-size:0.72rem;font-weight:650}

/* Container */
.wrap{max-width:1300px;margin:0 auto;padding:10px 16px 40px}
.sec-info{padding:16px 4px 6px;font-size:0.78rem;color:var(--text-3);font-weight:500}

/* Card grid — denser, info-forward */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:12px;padding:8px 0 24px}

/* Card — white, clean, shows everything */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;cursor:pointer;transition:border-color 0.15s,box-shadow 0.15s;display:flex;flex-direction:column;gap:8px}
.card:hover{border-color:var(--border-hover);box-shadow:0 2px 12px rgba(0,0,0,0.06)}

/* Author row */
.c-head{display:flex;align-items:center;gap:8px}
.c-head img{width:28px;height:28px;border-radius:50%;object-fit:cover;border:1px solid var(--border);flex-shrink:0;background:#e8e8e8}
.avt{width:28px;height:28px;border-radius:50%;background:var(--green-bg);color:var(--green);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.75rem;flex-shrink:0}
.c-name{font-weight:650;font-size:0.82rem;color:var(--text)}
.c-time{font-size:0.66rem;color:var(--text-3);margin-left:auto}
.c-tags{display:flex;gap:4px;flex-shrink:0;margin-left:6px}
.c-tag{font-size:0.6rem;padding:1px 6px;border-radius:4px;font-weight:600;background:var(--bg);color:var(--text-2)}
.c-tag-hot{background:var(--gold-bg);color:var(--gold)}

/* Match row */
.c-match{display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--bg);border-radius:4px;font-size:0.88rem}
.c-num{font-size:0.62rem;font-weight:700;color:var(--green);background:var(--green-bg);padding:2px 6px;border-radius:3px;font-family:var(--font-mono);flex-shrink:0}
.c-teams{font-weight:650;color:var(--text);flex:1}
.c-teams i{font-weight:400;color:var(--text-3);font-size:0.68rem;font-style:normal;margin:0 3px}
.c-ko{font-size:0.7rem;color:var(--green);font-weight:600;font-family:var(--font-mono);flex-shrink:0}

/* Prediction — FULL info shown, no hiding */
.c-pred{font-size:0.82rem;line-height:1.45;color:var(--text-2)}
.c-pred .c-line{display:flex;align-items:baseline;gap:6px;padding:1px 0}
.c-pred .c-line .lbl{font-size:0.62rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.3px;min-width:34px;flex-shrink:0}
.c-pred .c-line .val{font-weight:650;color:var(--green)}
.c-pred .c-sep{font-size:0.64rem;font-weight:700;color:var(--gold);margin-top:3px;padding-bottom:1px;border-bottom:1px solid var(--border);margin-bottom:2px}
.c-pred .c-raw{color:var(--text-2);white-space:pre-line;font-size:0.8rem;line-height:1.45}
.c-img{width:100%;border-radius:4px;overflow:hidden;border:1px solid var(--border)}
.c-img img{width:100%;height:auto;display:block;max-height:300px;object-fit:cover}
.c-foot{display:flex;justify-content:space-between;font-size:0.64rem;color:var(--text-3);padding-top:2px}

/* Modal — for image zoom and extra details */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:100;justify-content:center;align-items:center;padding:24px;backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}
.modal-overlay.show{display:flex}
.modal-sheet{background:#fff;border:1px solid var(--border);border-radius:12px;max-width:640px;width:100%;max-height:90vh;overflow-y:auto;padding:28px 24px;position:relative;box-shadow:0 16px 48px rgba(0,0,0,0.12);animation:modIn 0.18s ease-out}
@keyframes modIn{from{opacity:0;transform:translateY(8px) scale(0.98)}to{opacity:1;transform:translateY(0) scale(1)}}
.modal-sheet .d-author{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.modal-sheet .d-author img{width:40px;height:40px;border-radius:50%;object-fit:cover;border:1px solid var(--border);background:#e8e8e8}
.modal-sheet .d-name{font-weight:650;font-size:0.95rem}
.modal-sheet .d-time{font-size:0.7rem;color:var(--text-3);margin-top:1px}
.modal-sheet .d-match{background:var(--bg);border-radius:6px;padding:10px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:0.95rem;font-weight:650}
.modal-sheet .d-content{font-size:0.84rem;line-height:1.6;color:var(--text-2)}
.modal-sheet .d-content .d-line{display:flex;align-items:baseline;gap:8px;padding:4px 0}
.modal-sheet .d-content .d-line:not(:last-child){border-bottom:1px solid #f0f2ee}
.modal-sheet .d-content .d-label{font-size:0.64rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.3px;min-width:42px;flex-shrink:0}
.modal-sheet .d-content .d-value{font-weight:650;color:var(--text)}
.modal-sheet .d-image{width:100%;border-radius:6px;margin-top:10px;border:1px solid var(--border);cursor:pointer}
.modal-sheet .d-stats{display:flex;gap:20px;margin-top:14px;font-size:0.72rem;color:var(--text-3);padding-top:10px;border-top:1px solid var(--border)}

.lightbox{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.96);z-index:200;justify-content:center;align-items:center;cursor:zoom-out}
.lightbox.show{display:flex}
.lightbox img{max-width:95vw;max-height:95vh;border-radius:4px}

.empty{display:none;text-align:center;padding:60px 20px;color:var(--text-3)}
.empty p{margin-top:8px;font-size:0.86rem}

@media(max-width:800px){.grid{grid-template-columns:1fr}}
@media(max-width:480px){.header h1{font-size:1.1rem}.card{padding:12px 14px}}
@media(prefers-reduced-motion:reduce){.modal-sheet{animation:none}}
</style></head>
<body>
<div class="header"><h1>FIFA World Cup 2026</h1><div class="sub">BLOGGER PREDICTIONS</div></div>
<div class="bar"><label for="ds">Date</label><select id="ds" onchange="filter()"><option value="all">All</option></select><span class="badge" id="cnt"></span></div>
<div class="wrap" id="mc"></div>
<div class="empty" id="emp"><p>No predictions for this date</p></div>
<div class="modal-overlay" id="mod" onclick="if(event.target===this)closeMod()"><div class="modal-sheet" id="ms"></div></div>
<div class="lightbox" id="lb" onclick="closeLb()"><img id="lbImg" src="" alt=""></div>
<script>
var ENTRIES=__ENTRIES_JSON__;
var DATES=__DATES_JSON__;
function renderAll(){var h='';DATES.forEach(function(ds){var dc=ENTRIES.filter(function(e){return e.d===ds});if(!dc.length)return;var au={};dc.forEach(function(e){au[e.au]=1});h+='<div class="date-section" data-date="'+ds+'"><div class="sec-info">'+Object.keys(au).length+' bloggers &middot; '+dc.length+' picks</div><div class="grid">';dc.forEach(function(e){h+=renderCard(e)});h+='</div></div>'});document.getElementById('mc').innerHTML=h;document.getElementById('cnt').textContent=ENTRIES.length+' picks';var s=document.getElementById('ds');DATES.forEach(function(d){var o=document.createElement('option');o.value=d;o.textContent=d;s.appendChild(o)});if(DATES.length>0){s.value=DATES[0];filter()}document.getElementById('mc').addEventListener('click',function(e){var card=e.target.closest('.card');if(!card)return;var id=parseInt(card.getAttribute('data-id'));if(!id)return;showDetail(id)})}
function renderCard(e){var h='';h+='<div class="card" data-id="'+e.id+'">';
// Header
h+='<div class="c-head">';
if(e.av)h+='<img src="'+esc(e.av)+'" alt="" loading="lazy" onerror="this.style.display=\'none\'">';else h+='<span class="avt">'+esc((e.au||'?')[0])+'</span>';
h+='<div class="c-name">'+esc(e.au)+'</div>';
if(e.tg&&e.tg.length){h+='<div class="c-tags">';e.tg.forEach(function(t){h+='<span class="c-tag'+(t==='高胜率'?' c-tag-hot':'')+'">'+esc(t)+'</span>'});h+='</div>'}
h+='<div class="c-time">'+esc(e.tm||'')+'</div></div>';
// Match
if(e.mh&&e.ma){h+='<div class="c-match">';if(e.mn)h+='<span class="c-num">#'+esc(e.mn)+'</span>';h+='<span class="c-teams">'+esc(e.mh)+' <i>vs</i> '+esc(e.ma)+'</span>';if(e.mt)h+='<span class="c-ko">'+esc(e.mt)+'</span>';h+='</div>'}
// FULL predictions — all shown on card
var hasC=false;
if(e.ht&&e.pr){var lines=[];var ms=e.pr.matches||[];ms.forEach(function(m,idx){if(ms.length>1)lines.push('<div class="c-sep">Match '+(idx+1)+'</div>');if(m.direction)lines.push('<div class="c-line"><span class="lbl">Pick</span><span class="val">'+esc(m.direction)+'</span></div>');if(m.index_rec)lines.push('<div class="c-line"><span class="lbl">Index</span><span class="val">'+esc(m.index_rec)+'</span></div>');if(m.score_rec)lines.push('<div class="c-line"><span class="lbl">Score</span><span class="val">'+esc(m.score_rec)+'</span></div>');if(m.total_goals)lines.push('<div class="c-line"><span class="lbl">Goals</span><span class="val">'+esc(m.total_goals)+'</span></div>');if(!m.direction&&!m.index_rec&&!m.score_rec&&!m.total_goals&&m.raw)lines.push('<div class="c-raw">'+esc(m.raw)+'</div>')});if(lines.length){h+='<div class="c-pred">'+lines.join('')+'</div>';hasC=true}}
if(e.hi&&e.il){h+='<div class="c-img"><img src="'+esc(e.il)+'" alt="" loading="lazy" onclick="event.stopPropagation();openLb(\''+esc(e.il)+'\')"></div>';hasC=true}
if(!hasC)h+='<div class="c-pred"><div class="c-raw">Tap for details</div></div>';
h+='<div class="c-foot"><span>'+e.rn+' reads</span><span>'+e.bn+' buys</span></div></div>';return h}
function filter(){var d=document.getElementById('ds').value;var ss=document.querySelectorAll('.date-section'),t=0,v=false;ss.forEach(function(s){if(d==='all'||s.getAttribute('data-date')===d){s.style.display='';v=true;t+=s.querySelectorAll('.card').length}else s.style.display='none'});document.getElementById('cnt').textContent=t+' picks';document.getElementById('emp').style.display=v?'none':'block';document.getElementById('mc').style.display=v?'':''}
function showDetail(id){var d=ENTRIES.find(function(e){return e.id===id});if(!d)return;var h='';h+='<div class="d-author">';if(d.av)h+='<img src="'+esc(d.av)+'" alt="" onerror="this.style.display=\'none\'">';else h+='<span class="avt">'+esc((d.au||'?')[0])+'</span>';h+='<div><div class="d-name">'+esc(d.au)+'</div><div class="d-time">'+esc(d.tm||'')+'</div></div>';if(d.tg&&d.tg.length){h+='<div class="c-tags" style="margin-left:auto">';d.tg.forEach(function(x){h+='<span class="c-tag'+(x==='高胜率'?' c-tag-hot':'')+'">'+esc(x)+'</span>'});h+='</div>'}h+='</div>';if(d.mh&&d.ma){h+='<div class="d-match">';if(d.mn)h+='<span class="c-num">#'+esc(d.mn)+'</span>';h+='<span>'+esc(d.mh)+' <i>vs</i> '+esc(d.ma)+'</span>';if(d.mt)h+='<span class="c-ko" style="margin-left:auto">'+esc(d.mt)+'</span>';h+='</div>'}if(d.ht&&d.pr){h+='<div class="d-content">';var ms=d.pr.matches||[];if(ms.length){ms.forEach(function(m,i){if(i>0)h+='<div style="margin-top:12px"></div>';if(ms.length>1)h+='<div style="font-weight:650;color:var(--green);margin-bottom:3px">Match '+(i+1)+'</div>';if(m.teams)h+='<div class="d-line"><span class="d-label">Match</span><span class="d-value">'+esc(m.teams)+'</span></div>';if(m.direction)h+='<div class="d-line"><span class="d-label">Pick</span><span class="d-value">'+esc(m.direction)+'</span></div>';if(m.index_rec)h+='<div class="d-line"><span class="d-label">Index</span><span class="d-value">'+esc(m.index_rec)+'</span></div>';if(m.score_rec)h+='<div class="d-line"><span class="d-label">Score</span><span class="d-value">'+esc(m.score_rec)+'</span></div>';if(m.total_goals)h+='<div class="d-line"><span class="d-label">Goals</span><span class="d-value">'+esc(m.total_goals)+'</span></div>';if(!m.teams&&!m.direction&&!m.index_rec&&!m.score_rec&&!m.total_goals&&m.raw)h+='<div style="white-space:pre-line">'+esc(m.raw)+'</div>'})}else if(d.pr.raw){h+='<div style="white-space:pre-line">'+esc(d.pr.raw)+'</div>'}h+='</div>'}if(d.hi&&d.il){var isrc=esc(d.il);h+='<img class="d-image" src="'+isrc+'" alt="" onclick="openLb(\''+isrc+'\')">'}h+='<div class="d-stats"><span>Reads: '+(d.rn||0)+'</span><span>Buys: '+(d.bn||0)+'</span></div>';document.getElementById('ms').innerHTML=h;document.getElementById('mod').classList.add('show');document.body.style.overflow='hidden'}
function closeMod(){document.getElementById('mod').classList.remove('show');document.body.style.overflow=''}
function openLb(s){document.getElementById('lbImg').src=s;document.getElementById('lb').classList.add('show');document.body.style.overflow='hidden'}
function closeLb(){document.getElementById('lb').classList.remove('show');document.body.style.overflow=''}
function esc(s){if(!s)return'';return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
document.addEventListener('keydown',function(e){if(e.key==='Escape'){closeMod();closeLb()}});
renderAll();
</script>
</body></html>'''

def gen_html(ae):
    dates = sorted({e["d"] for e in ae}, reverse=True)
    return HTML_T.replace('__ENTRIES_JSON__', json.dumps(ae, ensure_ascii=False)).replace('__DATES_JSON__', json.dumps(dates, ensure_ascii=False))

def main():
    if len(sys.argv)<2: print("Usage: python generate_report.py <json>"); sys.exit(1)
    jp = sys.argv[1]
    if not Path(jp).exists(): print(f"ERROR: {jp}"); sys.exit(1)
    print("="*56); print("  World Cup 2026 — Predictions"); print("="*56)
    merge_json(jp); ae = load_all()
    print(f"  {len(ae)} entries | {sum(1 for e in ae if e['ht'])} text + {sum(1 for e in ae if e['hi'])} image")
    html = gen_html(ae); HTML.write_text(html, encoding="utf-8")
    print(f"  -> {HTML} ({len(html):,} bytes)")
    ds = {e["d"] for e in ae}; au = {e["au"] for e in ae}
    print(f"  Dates: {min(ds)}~{max(ds)} | Bloggers: {len(au)}")
    print(f"  Open: file:///{HTML}")

if __name__=="__main__": main()
