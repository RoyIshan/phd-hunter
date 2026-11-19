// Academic Positions collector (template).
// The site blocks scripts, so the listing pages are read inside a real browser tab.
// Do not run this file as is. Generate the ready-to-run version, filled with the
// fields and keywords from config/search.json:
//
//   python3 scripts/collector.py academicpositions
//
// then, in a browser tab open on https://academicpositions.com/find-jobs, execute the
// printed code, save the returned advert lines (everything after the first log line)
// to data/inbox/academicpositions.txt and run
//
//   python3 scripts/import_postings.py data/inbox/academicpositions.txt
//
// Output: one advert per line, path|title|institution|city|country|deadline|summary.
// Read-only: it requests public listing pages one at a time, with a pause.
// If the page shows a verification challenge, stop and let the user pass it
// themselves. Never try to get around it.

const FIELDS = /*FIELDS*/[];
const MAX_PAGES = /*MAX_PAGES*/15;
const ROLE = /phd|doctoral|doctorate|doktorand|research assistant|predoc/i;
const NOT_ROLE = /post-?doc/i;
const KEEP = /*KEEP*/null;  // theme keywords; null keeps every doctoral advert

const seen = new Map();
const log = {};
for (const field of FIELDS) {
  let kept = 0, pages = 0;
  for (let page = 1; page <= MAX_PAGES; page++) {
    const res = await fetch(`/jobs/field/${field}?page=${page}`, { credentials: "include" });
    if (!res.ok || !res.url.includes(field)) break;
    const doc = new DOMParser().parseFromString(await res.text(), "text/html");
    const cards = [...doc.querySelectorAll(".job-list-item")];
    if (!cards.length) break;
    pages++;
    for (const card of cards) {
      const ad = card.querySelector('a[href*="/ad/"]');
      if (!ad) continue;
      const flat = card.textContent.replace(/\s+/g, " ").trim();
      const kind = [...card.querySelectorAll('a[href*="/jobs/position/"]')].map(a => a.textContent.trim()).join(", ");
      const title = (ad.querySelector("h1,h2,h3,h4,h5,strong,b") || ad).textContent.replace(/\s+/g, " ").trim().split("  ")[0];
      if (!ROLE.test(kind + " " + title)) continue;
      const url = new URL(ad.getAttribute("href"), "https://academicpositions.com").href;
      const places = [...card.querySelectorAll('a[href*="/jobs/country/"]')].map(a => a.textContent.replace(/[,\s]+$/g, "").trim());
      const closing = flat.match(/Closing on:\s*(\d{4}-\d{2}-\d{2})/);
      const item = seen.get(url) || {
        source: "academicpositions", url, title: title.slice(0, 200),
        org: (card.querySelector('a[href*="/employer/"]') || {}).textContent?.trim() || "",
        city: places.length > 1 ? places[0] : "", country: places[places.length - 1] || "",
        deadline: closing ? closing[1] : "", summary: ad.textContent.replace(/\s+/g, " ").trim().slice(title.length).trim().slice(0, 280),
        field: "",
      };
      item.field = [...new Set((item.field ? item.field.split("; ") : []).concat(field))].join("; ");
      if (!seen.has(url)) kept++;
      seen.set(url, item);
    }
    if (cards.length < 30) break;
    await new Promise(r => setTimeout(r, 600));
  }
  log[field] = `${pages} pages, ${kept} new PhD-level adverts`;
}
const rows = [...seen.values()].filter(p => !NOT_ROLE.test(p.title) &&
  (!KEEP || KEEP.test(p.title + " " + p.summary + " " + p.field.replace(/-/g, " "))));
JSON.stringify(log) + "\n" + rows.map(p =>
  [p.url.replace("https://academicpositions.com/ad/", ""), p.title, p.org, p.city, p.country, p.deadline, p.summary.slice(0, 160)]
    .map(x => String(x).replace(/[\t\n|]/g, " ")).join("|")).join("\n");
