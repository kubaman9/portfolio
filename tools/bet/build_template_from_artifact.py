#!/usr/bin/env python3
"""Turn the live 'Kubaman Ledger' artifact HTML into a static, encrypted-page
template: strip the artifact-platform wrapper, remove all live db.use('db')
calls, embed data via a single DATA object substituted from __ARCHIVE_JSON__,
default the landing route to #/today, and link out to the day's artifact."""
import re

SRC = "/tmp/claude-0/-home-user-portfolio/a9c2409a-d630-58fa-b471-59e2b0923536/scratchpad/bet_build/raw_artifact.html"
OUT = "/tmp/claude-0/-home-user-portfolio/a9c2409a-d630-58fa-b471-59e2b0923536/scratchpad/bet_build/template_shell.html"

raw = open(SRC, encoding="utf-8").read()

# 1. Strip the artifact-platform wrapper on line 1 and the blank line 2.
lines = raw.split("\n")
assert lines[0].startswith("<!doctype html><html><head>")
assert lines[1] == ""
head = (
    '<!doctype html>\n'
    '<html lang="en" data-theme="dark"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<meta name="robots" content="noindex,nofollow">'
)
body = "\n".join(lines[2:])  # starts at <title>...
content = head + body
assert content.rstrip().endswith("</body></html>")

# 2. Replace the whole `var FALLBACK = {...};` literal with `var DATA = __ARCHIVE_JSON__;`
m = re.search(r'var FALLBACK = (\{.*?\});\n', content, re.S)
assert m, "FALLBACK literal not found"
fb_start, fb_end = m.span()
content = content[:fb_start] + "var DATA = __ARCHIVE_JSON__;\n" + content[fb_end:]

# 3. Drop the two comment lines above it that described the live-db architecture,
#    replace with an accurate one.
content = content.replace(
    '/* THE PAGE IS A RENDERER. History lives in the artifact db (index/meta, days/YYYY-MM-DD); this file never writes.\n'
    '   FALLBACK is the small snapshot embedded at publish time, shown when the db cannot run in this view.\n'
    '   HOME = the stats dashboard. DAILY VIEW = that day\'s picks first. */\n',
    '/* THE PAGE IS A RENDERER. All history ships baked into this file as DATA (index + days), built and\n'
    '   encrypted by make_bet.py from Mongo. There is no live db call and this file never writes anywhere.\n'
    '   HOME (#/) = the stats dashboard. #/today (default) and #/day/YYYY-MM-DD = that day\'s picks first. */\n',
)

# 4. getMeta/fbMeta: read straight from DATA, no fallback shim needed.
content = content.replace(
    'function fbMeta(){\n'
    '  if(!FALLBACK) return {days:[],kpi:{tiles:[]}};\n'
    '  return {latest_day:FALLBACK.day.date, days:[FALLBACK.entry], kpi:FALLBACK.kpi, bands:null, stats:null};\n'
    '}\n'
    'function getMeta(){ return state.meta||fbMeta(); }',
    'function getMeta(){ return (DATA&&DATA.index) || {days:[],kpi:{tiles:[]}}; }',
)

# 5. getDay: synchronous read from DATA.days, no async fetch.
content = content.replace(
    'function getDay(date){\n'
    '  if(state.days[date]) return Promise.resolve(state.days[date]);\n'
    '  if(!state.db) return Promise.resolve(null);\n'
    '  return state.db.doc("days/"+date).get().then(function(s){\n'
    '    if(s.exists){ state.days[date]=s.data(); return state.days[date]; } return null;\n'
    '  }).catch(function(){ return null; });\n'
    '}',
    'function getDay(date){ return (DATA&&DATA.days&&DATA.days[date])||null; }',
)

# 6. renderDay: no more loading/partial states, everything is already local.
content = content.replace(
    'function renderDay(date){\n'
    '  var tok=++state.token;\n'
    '  var fb=FALLBACK&&FALLBACK.day&&FALLBACK.day.date===date?FALLBACK.day:null;\n'
    '  var cached=state.days[date];\n'
    '  if(cached){ drawDay(cached,date,false); return; }\n'
    '  if(fb) drawDay(fb,date,true);\n'
    '  else if(state.dbStatus==="pending"){ app.innerHTML=dateline(date,"")+dbNote(); }\n'
    '  if(state.db){\n'
    '    getDay(date).then(function(doc){\n'
    '      if(tok!==state.token) return;\n'
    '      if(doc) drawDay(doc,date,false);\n'
    '      else if(fb) { drawDay(fb,date,true); }\n'
    '      else drawMissing(date);\n'
    '    });\n'
    '  } else if(state.dbStatus!=="pending" && !fb){ drawMissing(date); }\n'
    '}',
    'function renderDay(date){\n'
    '  var doc=getDay(date);\n'
    '  if(doc) drawDay(doc,date,false); else drawMissing(date);\n'
    '}',
)

# 7. loadAll: read straight from DATA.days, no Firestore collection call.
content = content.replace(
    'function loadAll(){\n'
    '  if(state.all) return Promise.resolve(state.all);\n'
    '  if(!state.db) return Promise.resolve(null);\n'
    '  return state.db.collection("days").get().then(function(snap){\n'
    '    var out=[]; snap.docs.forEach(function(d){ if(d.exists){ var x=d.data(); if(x&&x.date) out.push(x); } });\n'
    '    out.sort(function(a,b){ return a.date<b.date?-1:1; });\n'
    '    state.all=out; return out;\n'
    '  }).catch(function(){ return null; });\n'
    '}',
    'function loadAll(){\n'
    '  if(state.all) return Promise.resolve(state.all);\n'
    '  var out=Object.keys((DATA&&DATA.days)||{}).map(function(k){ return DATA.days[k]; });\n'
    '  out.sort(function(a,b){ return a.date<b.date?-1:1; });\n'
    '  state.all=out; return Promise.resolve(out);\n'
    '}',
)

# 8. dbNote/state: data is always present, so dbStatus is always "ok".
content = content.replace(
    'var state={db:null, dbStatus:"pending", meta:null, days:{}, all:null, token:0};',
    'var state={dbStatus:"ok", all:null};',
)
content = content.replace(
    'function dbNote(){\n'
    '  if(state.dbStatus==="unavailable") return \'<p class="note db-note">Archive unavailable in this view. Showing the snapshot embedded at publish time; history, other days and the stats need the database.</p>\';\n'
    '  if(state.dbStatus==="empty") return \'<p class="note db-note">The archive is empty (index/meta not written yet). Showing the embedded snapshot.</p>\';\n'
    '  if(state.dbStatus==="pending") return \'<p class="note db-note">Loading archive…</p>\';\n'
    '  return "";\n'
    '}',
    'function dbNote(){ return ""; }',
)

# 9. route(): default landing is #/today, not home; #/ is explicitly Home.
content = content.replace(
    'function route(keepScroll){\n'
    '  var h=location.hash||"", m=h.match(/^#\\/day\\/(\\d{4}-\\d{2}-\\d{2})/);\n'
    '  var lt=latestDay(); var rt=$("rail-today"); if(rt&&lt) rt.setAttribute("href","#/day/"+lt);\n'
    '  var meta=getMeta();\n'
    '  var latest=(meta.days||[]).slice().sort(function(a,b){return a.date<b.date?1:-1;})[0]||{};\n'
    '  $("r-rec").textContent=latest.record_after||"—";\n'
    '  $("r-u").textContent=latest.units_after==null?"—":money(latest.units_after)+"u";\n'
    '  $("r-u").className=latest.units_after<0?"neg":latest.units_after>0?"pos":"neutral";\n'
    '  $("r-open").textContent=latest.open==null?"—":latest.open;\n'
    '  $("r-card").textContent=latest.card_text||"—";\n'
    '  if(m) renderDay(m[1]); else renderHome();\n'
    '  if(!keepScroll) window.scrollTo(0,0);\n'
    '}\n'
    'window.addEventListener("hashchange",function(){ route(false); });\n'
    'route(false);\n'
    '(async function initDb(){\n'
    '  var t=setTimeout(function(){ if(state.dbStatus==="pending"){ state.dbStatus="unavailable"; route(true); } },12000);\n'
    '  var db=null;\n'
    '  try{ if(window.claude&&typeof window.claude.use==="function") db=await window.claude.use("db"); }catch(e){ db=null; }\n'
    '  clearTimeout(t);\n'
    '  if(!db){ state.dbStatus="unavailable"; route(true); return; }\n'
    '  state.db=db;\n'
    '  try{\n'
    '    var snap=await db.doc("index/meta").get();\n'
    '    if(snap.exists){ state.meta=snap.data(); state.dbStatus="ok"; } else { state.dbStatus="empty"; }\n'
    '  }catch(e){ state.dbStatus="unavailable"; state.db=null; }\n'
    '  route(true);\n'
    '})();',
    'function route(keepScroll){\n'
    '  var h=location.hash||"";\n'
    '  if(h===""||h==="#"){ location.replace("#/today"); return; }\n'
    '  var m=h.match(/^#\\/day\\/(\\d{4}-\\d{2}-\\d{2})/);\n'
    '  var lt=latestDay(); var rt=$("rail-today"); if(rt&&lt) rt.setAttribute("href","#/day/"+lt);\n'
    '  var meta=getMeta();\n'
    '  var latest=(meta.days||[]).slice().sort(function(a,b){return a.date<b.date?1:-1;})[0]||{};\n'
    '  $("r-rec").textContent=latest.record_after||"—";\n'
    '  $("r-u").textContent=latest.units_after==null?"—":money(latest.units_after)+"u";\n'
    '  $("r-u").className=latest.units_after<0?"neg":latest.units_after>0?"pos":"neutral";\n'
    '  $("r-open").textContent=latest.open==null?"—":latest.open;\n'
    '  $("r-card").textContent=latest.card_text||"—";\n'
    '  if(m) renderDay(m[1]);\n'
    '  else if(h==="#/today"){ var t=latestDay(); if(t) renderDay(t); else renderHome(); }\n'
    '  else renderHome();\n'
    '  if(!keepScroll) window.scrollTo(0,0);\n'
    '}\n'
    'window.addEventListener("hashchange",function(){ route(false); });\n'
    'route(false);',
)

# 10. Point the rail's Today link at #/today (a fixed route) instead of a
#     date that gets filled in after the fact, and make Home point at #/.
content = content.replace(
    '<span class="rail-links"><a class="navbtn" href="#/">Home</a><a class="navbtn" id="rail-today" href="#/">Today</a></span>',
    '<span class="rail-links"><a class="navbtn" href="#/">Home</a><a class="navbtn" id="rail-today" href="#/today">Today</a></span>',
)

# 11. Add a prominent artifact link on day pages, right under the masthead.
content = content.replace(
    "  var lead=(doc.alerts||[]).filter(function(a){return a.tone===\"lead\";})[0];\n"
    "  if(lead) h+=alertBox(lead);",
    "  if(doc.artifact_url_for_that_day) h+='<a class=\"todaybar\" href=\"'+esc(doc.artifact_url_for_that_day)+'\" target=\"_blank\" rel=\"noopener\"><span><b>Full briefing artifact</b><br><span class=\"wire-t\">The formatted daily ledger for '+esc(date)+'</span></span><span class=\"navbtn\">Open \\u203a</span></a>';\n"
    "  var lead=(doc.alerts||[]).filter(function(a){return a.tone===\"lead\";})[0];\n"
    "  if(lead) h+=alertBox(lead);",
)

# 12. Mobile fix: #r-card (the sticky rail's "today's card" summary) can be a
#     long free-text string and had no truncation, forcing horizontal scroll
#     on phones. Truncate it with an ellipsis under the same breakpoint that
#     already hides the rail-stat labels.
old_rule = "  .rail-in{gap:.75rem} .rail-stat i{display:none}"
assert old_rule in content
content = content.replace(
    old_rule,
    old_rule + "\n  #r-card{display:inline-block;max-width:34vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}",
)

assert "__ARCHIVE_JSON__" in content
assert "window.claude" not in content
assert "state.db" not in content
assert "FALLBACK" not in content

open(OUT, "w", encoding="utf-8").write(content)
print("wrote", OUT, len(content), "bytes")
