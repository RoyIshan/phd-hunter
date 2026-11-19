#!/usr/bin/env python3
"""Write dashboard.html: an offline, single-file view of the pipeline.

    python3 scripts/dashboard.py
"""
import csv
import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = dt.date.today()


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    store_path = ROOT / "data" / "postings.json"
    store = json.loads(store_path.read_text()) if store_path.exists() else {}
    postings = [
        {k: p.get(k, "") for k in ("id", "title", "org", "country", "deadline", "url", "source",
                                    "prefilter", "fit", "status", "flags", "verdict", "summary", "signals", "salary", "report")}
        for p in store.values()
        if p.get("status") in ("new", "seen", "evaluated", "tracked") and p.get("prefilter", 0) >= 15
    ]
    data = {
        "today": TODAY.isoformat(),
        "postings": postings,
        "tracker": read_csv(ROOT / "data" / "tracker.csv"),
        "contacts": read_csv(ROOT / "data" / "contacts.csv"),
        "stored": len(store),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.replace("__DATA__", payload).replace("__DATE__", html.escape(TODAY.strftime("%d %B %Y")))
    out = ROOT / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out.name}: {len(postings)} postings, {len(data['tracker'])} tracked, {len(data['contacts'])} contacts.")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhD pipeline</title>
<style>
:root{--bg:#f6f5f1;--card:#fff;--ink:#1d2327;--mute:#667078;--line:#e2dfd6;--accent:#1f5f8b;--good:#2f7d4f;--warn:#b26a00;--bad:#a8323a;--chip:#eef2f5}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15181b;--card:#1e2327;--ink:#e8eaec;--mute:#98a2ab;--line:#2f363c;--accent:#7db8e0;--good:#6cc08b;--warn:#e0a94e;--bad:#e5767d;--chip:#2a3137}}
:root[data-theme="dark"]{--bg:#15181b;--card:#1e2327;--ink:#e8eaec;--mute:#98a2ab;--line:#2f363c;--accent:#7db8e0;--good:#6cc08b;--warn:#e0a94e;--bad:#e5767d;--chip:#2a3137}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:24px;margin:0 0 2px;letter-spacing:-.01em}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.07em;color:var(--mute);margin:34px 0 10px;font-weight:600}
.sub{color:var(--mute);margin:0 0 20px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:26px;font-variant-numeric:tabular-nums;line-height:1.1}
.stat span{color:var(--mute);font-size:13px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}
input,select{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
input[type=search]{flex:1;min-width:180px}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:720px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);cursor:pointer;white-space:nowrap;user-select:none}
tr:last-child td{border-bottom:0}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.small{color:var(--mute);font-size:13px}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:1px 9px;font-size:12px;margin:2px 4px 0 0;white-space:nowrap}
.good{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.empty{padding:18px;color:var(--mute)}
ul.due{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--line);border-radius:10px}
ul.due li{padding:9px 14px;border-bottom:1px solid var(--line);display:flex;gap:12px}
ul.due li:last-child{border-bottom:0}
.board{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.col{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;min-height:70px}
.col h3{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);display:flex;justify-content:space-between}
.tile{border:1px solid var(--line);border-radius:8px;padding:6px 8px;margin-top:6px;font-size:13px;line-height:1.35}
.tile b{display:block;font-weight:600}
.col.none{opacity:.55}
ul.due .d{min-width:64px;font-variant-numeric:tabular-nums;font-weight:600}
</style>
</head>
<body>
<main>
<h1>PhD pipeline</h1>
<p class="sub">Generated __DATE__. Refresh with <code>python3 scripts/dashboard.py</code>.</p>
<div class="stats" id="stats"></div>

<h2>Coming up</h2>
<ul class="due" id="due"></ul>

<h2>Pipeline</h2>
<div class="board" id="board"></div>

<h2>Applications</h2>
<div class="wrap"><table id="tracker"></table></div>

<h2>Scanned positions</h2>
<div class="bar">
  <input type="search" id="q" placeholder="Filter by title, institution, keyword">
  <select id="country"><option value="">All countries</option></select>
  <select id="state"><option value="">All</option><option value="evaluated">Evaluated</option><option value="new">Not yet evaluated</option><option value="clear">No gate flags</option></select>
</div>
<div class="wrap"><table id="postings"></table></div>

<h2>Outreach</h2>
<div class="wrap"><table id="contacts"></table></div>
</main>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const days = iso => { if (!iso) return null; const t = Date.parse(iso); return isNaN(t) ? null : Math.round((t - Date.parse(D.today)) / 864e5); };
const dl = iso => { const d = days(iso); if (d === null) return '<span class="small">none listed</span>';
  const cls = d < 0 ? "bad" : d <= 10 ? "warn" : ""; return `<span class="${cls}">${esc(iso)}</span> <span class="small">${d < 0 ? "closed" : d + " d"}</span>`; };
const link = (u, t) => u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t);

const open = ["discovered","evaluated","shortlisted","contacted","drafting"];
const count = s => D.tracker.filter(r => s.includes(r.status)).length;
document.getElementById("stats").innerHTML = [
  [D.postings.length, "positions worth a look"],
  [D.postings.filter(p => p.fit).length, "evaluated"],
  [count(open), "in preparation"],
  [count(["applied"]), "applied, waiting"],
  [count(["interview","offer","accepted"]), "interviews and offers"],
  [count(["rejected"]), "rejected"],
].map(([n, l]) => `<div class="stat"><b>${n}</b><span>${l}</span></div>`).join("");

const due = [];
D.tracker.forEach(r => { const d = days(r.deadline);
  if (open.includes(r.status) && d !== null && d >= -1 && d <= 30) due.push([d, `Deadline: ${esc(r.institution)}, ${esc(r.position)} <span class="chip">${esc(r.status)}</span>`]);
  const n = days(r.next_date); if (r.next_action && n !== null && n <= 30) due.push([n, `${esc(r.next_action)} <span class="small">${esc(r.institution)}</span>`]); });
D.postings.forEach(p => { const d = days(p.deadline); if (p.fit >= 3.8 && p.status !== "tracked" && d !== null && d >= 0 && d <= 21) due.push([d, `Strong fit not yet tracked: ${link(p.url, p.title)} <span class="chip">fit ${p.fit}</span>`]); });
due.sort((a, b) => a[0] - b[0]);
document.getElementById("due").innerHTML = due.length ? due.map(([d, t]) => `<li><span class="d ${d <= 7 ? "warn" : ""}">${d} d</span><span>${t}</span></li>`).join("") : '<li class="empty">Nothing dated in the next 30 days.</li>';

const stages = [["Shortlist", ["discovered","evaluated","shortlisted"]], ["In contact", ["contacted"]], ["Drafting", ["drafting"]], ["Applied", ["applied"]],
  ["Interview", ["interview"]], ["Offer", ["offer","accepted"]], ["Closed", ["rejected","withdrawn","expired","skipped"]], ["To confirm", ["unverified"]]];
document.getElementById("board").innerHTML = stages.map(([name, sts]) => { const rs = D.tracker.filter(r => sts.includes(r.status));
  return `<div class="col ${rs.length ? "" : "none"}"><h3><span>${name}</span><span>${rs.length}</span></h3>` + rs.slice(0, 6).map(r => { const d = days(r.deadline);
    return `<div class="tile"><b>${esc(r.institution)}</b>${esc(r.position.slice(0, 60))}<div class="small">${esc(r.tid)}${r.fit ? " · fit " + esc(r.fit) : ""}${d !== null && d >= 0 && open.includes(r.status) ? ` · <span class="${d <= 7 ? "warn" : ""}">${d} d</span>` : ""}</div></div>`; }).join("") +
    (rs.length > 6 ? `<div class="small" style="margin-top:6px">+ ${rs.length - 6} more</div>` : "") + "</div>"; }).join("");

function table(id, cols, rows, emptyText) {
  const el = document.getElementById(id); let sort = null, dir = 1;
  const draw = () => { const r = sort === null ? rows : [...rows].sort((a, b) => { const x = cols[sort].val(a), y = cols[sort].val(b); return (x > y ? 1 : x < y ? -1 : 0) * dir; });
    el.innerHTML = "<thead><tr>" + cols.map((c, i) => `<th data-i="${i}">${c.h}${sort === i ? (dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("") + "</tr></thead><tbody>" +
      (r.length ? r.map(x => "<tr>" + cols.map(c => `<td class="${c.cls || ""}">${c.cell(x)}</td>`).join("") + "</tr>").join("") : `<tr><td class="empty" colspan="${cols.length}">${emptyText}</td></tr>`) + "</tbody>"; };
  el.onclick = e => { const th = e.target.closest("th"); if (!th) return; const i = +th.dataset.i; dir = sort === i ? -dir : 1; sort = i; draw(); };
  draw(); return r => { rows = r; draw(); };
}

table("tracker", [
  {h: "ID", val: r => r.tid, cell: r => esc(r.tid), cls: "n"},
  {h: "Status", val: r => r.status, cell: r => `<span class="chip">${esc(r.status)}</span>`},
  {h: "Fit", val: r => +r.fit || 0, cell: r => esc(r.fit || "–"), cls: "n"},
  {h: "Position", val: r => r.position, cell: r => link(r.url, r.position) + `<div class="small">${esc(r.institution)}${r.country ? ", " + esc(r.country) : ""}${r.supervisor ? " · " + esc(r.supervisor) : ""}</div>`},
  {h: "Deadline", val: r => r.deadline || "9999", cell: r => dl(r.deadline), cls: "n"},
  {h: "Next", val: r => r.next_date || "9999", cell: r => esc(r.next_action || "") + (r.next_date ? ` <span class="small">${esc(r.next_date)}</span>` : "") + (r.notes ? `<div class="small">${esc(r.notes)}</div>` : "")},
], D.tracker, "No applications tracked yet.");

const countries = [...new Set(D.postings.map(p => p.country).filter(Boolean))].sort();
document.getElementById("country").innerHTML += countries.map(c => `<option>${esc(c)}</option>`).join("");
const base = [...D.postings].sort((a, b) => (b.fit || 0) - (a.fit || 0) || b.prefilter - a.prefilter);
const redraw = table("postings", [
  {h: "Fit", val: p => +p.fit || 0, cell: p => p.fit ? `<b class="${p.fit >= 3.8 ? "good" : p.fit < 3.5 ? "bad" : ""}">${p.fit}</b>` : "–", cls: "n"},
  {h: "Pre", val: p => p.prefilter, cell: p => p.prefilter, cls: "n"},
  {h: "Position", val: p => p.title, cell: p => link(p.url, p.title) + `<div class="small">${esc(p.org)} · ${esc(p.source)} · <code>${esc(p.id)}</code></div>` + (p.flags || []).map(f => `<span class="chip ${/^gate|blocks/.test(f) ? "bad" : /^urgent/.test(f) ? "warn" : ""}">${esc(f)}</span>`).join("") + (p.signals || []).filter(x => !/^lang-required/.test(x)).map(f => `<span class="chip">${esc(f)}</span>`).join("") + (p.salary ? `<div class="small">${esc(p.salary)}</div>` : "") + (p.verdict ? `<div class="small">${esc(p.verdict)}${p.report ? " · " + esc(p.report) : ""}</div>` : "")},
  {h: "Country", val: p => p.country, cell: p => esc(p.country)},
  {h: "Deadline", val: p => p.deadline || "9999", cell: p => dl(p.deadline), cls: "n"},
], base, "No postings match. Run the scan, or loosen the filter.");
const apply = () => { const q = document.getElementById("q").value.toLowerCase(), c = document.getElementById("country").value, s = document.getElementById("state").value;
  redraw(base.filter(p => (!q || (p.title + " " + p.org + " " + p.summary).toLowerCase().includes(q)) && (!c || p.country === c) && (!s || (s === "evaluated" ? !!p.fit : s === "clear" ? !(p.flags || []).some(f => /^gate|blocks/.test(f)) : !p.fit)))); };
["q", "country", "state"].forEach(id => document.getElementById(id).addEventListener("input", apply));

table("contacts", [
  {h: "Date", val: c => c.date, cell: c => esc(c.date), cls: "n"},
  {h: "Status", val: c => c.status, cell: c => `<span class="chip">${esc(c.status)}</span>`},
  {h: "Person", val: c => c.name, cell: c => esc(c.name) + `<div class="small">${esc(c.role)}${c.role && c.institution ? ", " : ""}${esc(c.institution)}</div>`},
  {h: "For", val: c => c.tid, cell: c => esc(c.tid)},
  {h: "Notes", val: c => c.notes, cell: c => esc(c.notes)},
], D.contacts, "No outreach logged yet.");
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
