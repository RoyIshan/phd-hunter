#!/usr/bin/env python3
"""Draw the README artwork as self-contained SVG cards (no web fonts, scripts or external references).

    python3 docs/assets/build_assets.py            # rewrites the four .svg files next to this script

Standard library only. Edit the text or numbers here, not in the SVGs.
"""
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape as esc

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

BG0, BG1, SURF, LINE = "#080d1a", "#101830", "#131c38", "#26335c"
TXT, MUT = "#e8edf8", "#8d9ac0"
TEAL, VIO, AMB, GRN, RED, BLU = "#2dd4bf", "#a78bfa", "#fbbf24", "#4ade80", "#f87171", "#60a5fa"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

BASE_CSS = f"""
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none !important}}}}
"""


def svg(w, h, title, desc, body, css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-labelledby="t d">\n<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc)}</desc>\n'
        f"<defs>{defs}</defs>\n<style>{BASE_CSS}{css}</style>\n{body}\n</svg>\n"
    )


def card(w, h, rx=22):
    return (
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="url(#bg)"/>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="none" stroke="{LINE}"/>'
    )


BG_DEF = (
    f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/>'
    f'<stop offset="1" stop-color="{BG1}"/></linearGradient>'
)


def pill(cx, cy, text, color, size=14, pad=34):
    w = len(text) * size * 0.58 + pad
    return (
        f'<rect x="{cx - w/2:.1f}" y="{cy - 16}" width="{w:.1f}" height="32" rx="16" fill="{color}" fill-opacity="0.12" '
        f'stroke="{color}" stroke-opacity="0.55"/>'
        f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="s" font-size="{size}" font-weight="600" fill="{color}">{esc(text)}</text>'
    )


def pill_row(x, cy, items, size=14, pad=34, gap=14):
    out, cur = "", x
    for text, col in items:
        w = len(text) * size * 0.58 + pad
        out += pill(cur + w / 2, cy, text, col, size, pad)
        cur += w + gap
    return out


# ---------------------------------------------------------------- hero
def hero():
    W, H = 1200, 420
    cx, cy = 960, 212
    rings = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="1.2"/>' for r in (52, 104, 156, 208)
    )
    cross = (
        f'<line x1="{cx-216}" y1="{cy}" x2="{cx+216}" y2="{cy}" stroke="{LINE}"/>'
        f'<line x1="{cx}" y1="{cy-216}" x2="{cx}" y2="{cy+216}" stroke="{LINE}"/>'
    )
    # sweep wedge, 42 degrees
    R = 208
    a0, a1 = math.radians(-70), math.radians(-28)
    p0 = (cx + R * math.cos(a0), cy + R * math.sin(a0))
    p1 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
    wedge = (
        f'<g class="sweep"><path d="M{cx} {cy} L{p0[0]:.1f} {p0[1]:.1f} A{R} {R} 0 0 1 {p1[0]:.1f} {p1[1]:.1f} Z" '
        f'fill="url(#wedge)"/><line x1="{cx}" y1="{cy}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="{TEAL}" stroke-opacity="0.8" stroke-width="1.5"/></g>'
    )
    # blips: (angle deg, radius, colour, label)
    blips = [
        (-52, 150, TEAL, "NL"), (-12, 98, TEAL, "SE"), (24, 170, AMB, "DE"), (62, 120, TEAL, "NO"),
        (118, 150, GRN, "CH"), (160, 90, AMB, "FI"), (205, 160, MUT, ""), (238, 110, TEAL, "DK"),
        (262, 180, MUT, ""), (300, 70, AMB, ""), (330, 175, MUT, ""), (85, 190, MUT, ""),
    ]
    bl = ""
    for i, (ang, r, col, lab) in enumerate(blips):
        x = cx + r * math.cos(math.radians(ang))
        y = cy + r * math.sin(math.radians(ang))
        bl += (
            f'<circle class="pulse" style="animation-delay:{i*0.45:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" stroke="{col}" stroke-opacity="0.6"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col}"/>'
        )
        if lab:
            bl += (
                f'<text x="{x+9:.1f}" y="{y-8:.1f}" class="m" font-size="12" font-weight="700" fill="{col}" fill-opacity="0.95">{lab}</text>'
            )
    # reticle mark
    ret = (
        f'<g transform="translate(64 96)" fill="none" stroke="{TEAL}" stroke-width="3" stroke-linecap="round">'
        f'<circle cx="0" cy="0" r="14"/><path d="M-26 0H-10M10 0H26M0 -26V-10M0 10V26"/><circle cx="0" cy="0" r="3" fill="{TEAL}" stroke="none"/></g>'
    )
    body = (
        card(W, H, 26)
        + f'<rect width="{W}" height="{H}" rx="26" fill="url(#dots)"/>'
        + rings + cross + wedge + bl + ret
        + f'<text x="104" y="104" class="s" font-size="15" font-weight="700" letter-spacing="3.5" fill="{TEAL}">FOR EUROPE · LOCAL · OPEN SOURCE</text>'
        + f'<text x="60" y="196" class="s" font-size="80" font-weight="800" letter-spacing="-3" fill="{TXT}">phd-hunter</text>'
        + f'<text x="62" y="244" class="s" font-size="27" font-weight="600" fill="{TXT}">Find funded PhD positions across Europe.</text>'
        + f'<text x="62" y="278" class="s" font-size="19" fill="{MUT}">Check eligibility. Research the people. Draft in your own voice.</text>'
        + f'<text x="62" y="316" class="s" font-size="21" font-weight="700" fill="{AMB}">You read everything. You press submit.</text>'
        + pill_row(62, 372, [("Eligibility gates first", TEAL), ("Supervisors researched", VIO), ("Checked against your CV", GRN)])
    )
    defs = (
        BG_DEF
        + f'<linearGradient id="wedge" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.0"/>'
        f'<stop offset="1" stop-color="{TEAL}" stop-opacity="0.38"/></linearGradient>'
        + f'<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{LINE}" fill-opacity="0.55"/></pattern>'
    )
    css = f"""
.sweep{{transform-origin:{cx}px {cy}px;animation:sw 7s linear infinite}}
@keyframes sw{{to{{transform:rotate(360deg)}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pl 3.6s ease-out infinite}}
@keyframes pl{{0%{{transform:scale(1);opacity:.7}}100%{{transform:scale(2.6);opacity:0}}}}
"""
    return svg(
        W, H, "phd-hunter",
        "Banner: a radar sweeping over blips labelled with European country codes. phd-hunter, a local PhD hunter for Europe. You read everything. You press submit.",
        body, css, defs,
    )


# ---------------------------------------------------------------- pipeline
def pipeline():
    W, H = 1200, 408
    nodes = [
        ("1", "/setup", "profile and voice", TEAL),
        ("2", "/scan", "9 boards, parallel", TEAL),
        ("3", "/rank", "short-form scores", BLU),
        ("4", "/evaluate", "gates, fit, people", BLU),
        ("5", "/outreach", "briefs and drafts", VIO),
        ("6", "/apply", "CV, letter, pack", VIO),
        ("7", "/interview", "panel and mock", AMB),
        ("8", "/status", "deadlines, funnel", GRN),
    ]
    x0, step, nw, ny, nh = 52, 140, 116, 144, 84
    yc = ny + nh / 2
    body = card(W, H) + (
        f'<text x="52" y="58" class="s" font-size="26" font-weight="700" fill="{TXT}">From an empty profile to a tracked application</text>'
        f'<text x="52" y="86" class="s" font-size="15" fill="{MUT}">Eight stops on the main road. Side roads below and above.</text>'
    )
    body += f'<line class="flow" x1="40" y1="{yc}" x2="{W-40}" y2="{yc}" stroke="{TEAL}" stroke-opacity="0.65" stroke-width="2.5" stroke-dasharray="7 7"/>'
    for i in range(len(nodes) - 1):
        gx = x0 + i * step + nw + (step - nw) / 2
        body += f'<path d="M{gx-4} {yc-6} L{gx+5} {yc} L{gx-4} {yc+6} Z" fill="{TEAL}"/>'
    for i, (num, cmd, cap, col) in enumerate(nodes):
        x = x0 + i * step
        body += (
            f'<rect x="{x}" y="{ny}" width="{nw}" height="{nh}" rx="14" fill="{SURF}" stroke="{col}" stroke-opacity="0.7" stroke-width="1.5"/>'
            f'<circle cx="{x+20}" cy="{ny+20}" r="11" fill="{col}" fill-opacity="0.18" stroke="{col}"/>'
            f'<text x="{x+20}" y="{ny+25}" text-anchor="middle" class="m" font-size="13" font-weight="700" fill="{col}">{num}</text>'
            f'<text x="{x+nw/2}" y="{ny+55}" text-anchor="middle" class="m" font-size="16" font-weight="700" fill="{TXT}">{esc(cmd)}</text>'
            f'<text x="{x+nw/2}" y="{ny+74}" text-anchor="middle" class="s" font-size="11.5" fill="{MUT}">{esc(cap)}</text>'
        )
    # side roads: (node index, label, caption, above?)
    side = [
        (1, "/digest", "routine check", False),
        (3, "/compare", "2 to 6, side by side", False),
        (4, "/prospect", "before an advert exists", True),
        (5, "/proposal", "from papers you read", False),
        (7, "/inbox", "mail to tracker updates", False),
    ]
    for idx, lab, cap, above in side:
        cxn = x0 + idx * step + nw / 2
        if above:
            cy_ = 112
            y1, y2 = cy_ + 16, ny
        else:
            cy_ = 284
            y1, y2 = ny + nh, cy_ - 16
        body += f'<line x1="{cxn}" y1="{y1}" x2="{cxn}" y2="{y2}" stroke="{LINE}" stroke-width="2" stroke-dasharray="3 4"/>'
        body += (
            f'<rect x="{cxn-48}" y="{cy_-16}" width="96" height="32" rx="16" fill="{BG0}" stroke="{LINE}"/>'
            f'<text x="{cxn}" y="{cy_+5}" text-anchor="middle" class="m" font-size="13" font-weight="700" fill="{TXT}">{esc(lab)}</text>'
        )
        capy = cy_ - 24 if above else cy_ + 34
        body += f'<text x="{cxn}" y="{capy}" text-anchor="middle" class="s" font-size="11.5" fill="{MUT}">{esc(cap)}</text>'
    # bottom strip
    body += (
        f'<rect x="52" y="340" width="{W-104}" height="44" rx="12" fill="{AMB}" fill-opacity="0.09" stroke="{AMB}" stroke-opacity="0.45"/>'
        f'<text x="{W/2}" y="368" text-anchor="middle" class="s" font-size="16" font-weight="600" fill="{TXT}">'
        f'Every stop ends in a draft or a recommendation. <tspan fill="{AMB}">Deciding, sending and submitting stay yours.</tspan></text>'
    )
    css = ".flow{animation:fl 1.4s linear infinite}@keyframes fl{to{stroke-dashoffset:-14}}"
    return svg(
        W, H, "The phd-hunter route",
        "Eight stops: setup, scan, rank, evaluate, outreach, apply, interview, status. Side roads: digest, compare, prospect, proposal, inbox. Deciding, sending and submitting stay with the candidate.",
        body, css, BG_DEF,
    )


# ---------------------------------------------------------------- fit
def fit():
    W, H = 1200, 566
    body = card(W, H) + (
        f'<text x="52" y="58" class="s" font-size="26" font-weight="700" fill="{TXT}">Eligibility first. Then an honest score.</text>'
        f'<text x="52" y="86" class="s" font-size="15" fill="{MUT}">The same rubric drives both the full report (evaluate) and the short form (rank).</text>'
    )
    # left panel: gates
    lx, ly, lw, lh = 52, 112, 396, 340
    body += f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="18" fill="{SURF}" stroke="{LINE}"/>'
    body += f'<text x="{lx+24}" y="{ly+36}" class="s" font-size="13" font-weight="700" letter-spacing="2.5" fill="{TEAL}">STEP 0 · EIGHT GATES</text>'
    gates = ["Open", "Doctoral role", "Funding", "Degree", "MSCA mobility", "Language", "Credits and grades", "Deal-breakers"]
    for i, g in enumerate(gates):
        col, row = i % 2, i // 2
        gx, gy = lx + 24 + col * 180, ly + 58 + row * 52
        body += (
            f'<rect x="{gx}" y="{gy}" width="168" height="40" rx="10" fill="{BG0}" stroke="{LINE}"/>'
            f'<circle cx="{gx+20}" cy="{gy+20}" r="6" fill="none" stroke="{TEAL}" stroke-width="2"/>'
            f'<path d="M{gx+17} {gy+20} l2.4 2.6 l4.4 -5" fill="none" stroke="{TEAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<text x="{gx+36}" y="{gy+25}" class="s" font-size="14" font-weight="600" fill="{TXT}">{esc(g)}</text>'
        )
    body += (
        f'<text x="{lx+24}" y="{ly+290}" class="s" font-size="14" fill="{TXT}">Any failed gate caps the score at <tspan font-weight="700" fill="{RED}">2.0</tspan>.</text>'
        f'<text x="{lx+24}" y="{ly+314}" class="s" font-size="14" fill="{MUT}">Unknown is not a pass. It becomes <tspan class="m" font-weight="700" fill="{AMB}">CHECK</tspan>.</text>'
    )
    # arrow
    body += (
        f'<path d="M{lx+lw+14} 282 H{lx+lw+54}" stroke="{TEAL}" stroke-width="3" stroke-linecap="round"/>'
        f'<path d="M{lx+lw+46} 272 L{lx+lw+58} 282 L{lx+lw+46} 292 Z" fill="{TEAL}"/>'
    )
    # right panel: dimensions
    rx0, rw = 520, 628
    body += f'<rect x="{rx0}" y="{ly}" width="{rw}" height="{lh}" rx="18" fill="{SURF}" stroke="{LINE}"/>'
    body += f'<text x="{rx0+24}" y="{ly+36}" class="s" font-size="13" font-weight="700" letter-spacing="2.5" fill="{VIO}">SEVEN WEIGHTED DIMENSIONS</text>'
    dims = [
        ("Research fit", 30), ("Methods fit", 15), ("Eligibility and requirements", 15), ("Supervisor and group", 15),
        ("Funding and conditions", 10), ("Odds", 10), ("Place and life", 5),
    ]
    for i, (name, wgt) in enumerate(dims):
        y = ly + 66 + i * 38
        tx, tw = rx0 + 290, 250
        body += (
            f'<text x="{rx0+24}" y="{y+5}" class="s" font-size="15" fill="{TXT}">{esc(name)}</text>'
            f'<rect x="{tx}" y="{y-8}" width="{tw}" height="14" rx="7" fill="{BG0}" stroke="{LINE}"/>'
            f'<rect x="{tx}" y="{y-8}" width="{tw*wgt/30:.1f}" height="14" rx="7" fill="{VIO}" fill-opacity="{0.55 + 0.45*wgt/30:.2f}"/>'
            f'<text x="{tx+tw+22}" y="{y+5}" class="m" font-size="15" font-weight="700" fill="{TXT}">{wgt}%</text>'
        )
    # verdict strip
    segs = [("below 3.5", "Skip", RED), ("3.5 to 3.7", "Maybe", AMB), ("3.8 to 4.2", "Apply", TEAL), ("4.3 to 5.0", "Apply, priority", GRN)]
    sw, sy = (W - 104 - 3 * 12) / 4, 478
    for i, (rng, lab, col) in enumerate(segs):
        x = 52 + i * (sw + 12)
        body += (
            f'<rect x="{x:.1f}" y="{sy}" width="{sw:.1f}" height="56" rx="14" fill="{col}" fill-opacity="0.13" stroke="{col}" stroke-opacity="0.7"/>'
            f'<text x="{x+22:.1f}" y="{sy+34}" class="s" font-size="18" font-weight="800" fill="{col}">{esc(lab)}</text>'
            f'<text x="{x+sw-22:.1f}" y="{sy+34}" text-anchor="end" class="m" font-size="14" fill="{MUT}">{esc(rng)}</text>'
        )
    return svg(
        W, H, "Eligibility gates, weighted fit score and verdict bands",
        "Eight gates run first: open, doctoral role, funding, degree, MSCA mobility, language, credits and grades, deal-breakers. A failed gate caps the score at 2.0. Then seven weighted dimensions: research fit 30, methods fit 15, eligibility 15, supervisor and group 15, funding 10, odds 10, place and life 5. Verdict: below 3.5 skip, 3.5 to 3.7 maybe, 3.8 to 4.2 apply, 4.3 to 5.0 apply with priority.",
        body, "", BG_DEF,
    )


# ---------------------------------------------------------------- terminal
def terminal():
    W, H = 1000, 600
    body = (
        f'<rect width="{W}" height="{H}" rx="16" fill="#0b1122"/>'
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{LINE}"/>'
        f'<path d="M0 16 a16 16 0 0 1 16 -16 H{W-16} a16 16 0 0 1 16 16 V44 H0 Z" fill="#121a33"/>'
        f'<line x1="0" y1="44" x2="{W}" y2="44" stroke="{LINE}"/>'
        f'<circle cx="26" cy="22" r="6.5" fill="#f87171"/><circle cx="48" cy="22" r="6.5" fill="{AMB}"/><circle cx="70" cy="22" r="6.5" fill="{GRN}"/>'
        f'<text x="{W/2}" y="27" text-anchor="middle" class="s" font-size="13" fill="{MUT}">illustration: a fictional candidate and a fictional position</text>'
    )
    L = 32
    y = 84
    lh = 24

    def t(x, yy, txt, fill=TXT, weight=400, size=15, extra=""):
        return f'<text x="{x}" y="{yy}" class="m" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{esc(txt)}</text>'

    body += t(L, y, ">", TEAL, 700) + t(L + 22, y, "/phd-hunter evaluate https://example.org/jobs/phd-1234", TXT, 600)
    y += lh * 1.6
    rows = [
        ("Still open?", "yes, deadline 2027-01-12 (54 days)", GRN),
        ("Gates", "7 pass, 1 CHECK: English test score not in the profile", AMB),
        ("People", "Prof. A. Example, group page and 3 recent papers read", TXT),
    ]
    for lab, val, col in rows:
        body += t(L + 22, y, lab, MUT) + t(L + 170, y, val, col)
        y += lh
    y += lh * 0.6
    body += t(L, y, "PhD Position in Computational Semantics — University of Example, ES", TXT, 700)
    y += lh
    body += t(L, y, "Score 4.1 / 5 — Apply · Deadline 2027-01-12 (54 days) · https://example.org/jobs/phd-1234", TEAL, 600, 14.5)
    y += lh * 1.4
    dims = [
        ("Research fit", 4.5, 30), ("Methods fit", 4.0, 15), ("Eligibility and requirements", 4.0, 15),
        ("Supervisor and group", 4.0, 15), ("Funding and conditions", 4.0, 10), ("Odds", 3.5, 10), ("Place and life", 4.0, 5),
    ]
    for name, sc, wt in dims:
        bx, bw = 330, 280
        body += t(L + 22, y, name, TXT)
        body += (
            f'<rect x="{bx}" y="{y-12}" width="{bw}" height="12" rx="6" fill="{BG1}" stroke="{LINE}"/>'
            f'<rect x="{bx}" y="{y-12}" width="{bw*sc/5:.1f}" height="12" rx="6" fill="{VIO}" fill-opacity="{0.45 + 0.1*sc:.2f}"/>'
        )
        body += t(bx + bw + 22, y, f"{sc:.1f}", TXT, 700) + t(bx + bw + 74, y, f"{wt}%", MUT)
        y += lh
    y += lh * 0.5
    body += t(L + 22, y, "In ", GRN, 700) + t(L + 62, y, "the thesis question is close to the project's core question")
    y += lh
    body += t(L + 22, y, "Out", AMB, 700) + t(L + 62, y, "no peer-reviewed publication yet")
    y += lh
    body += t(L + 22, y, "CHECK", AMB, 700) + t(L + 90, y, "ask the contact person whether a language test is required")
    y += lh * 1.3
    body += t(L + 22, y, "Next: /phd-hunter outreach, /phd-hunter apply, or skip. Your call.", MUT)
    y += lh * 1.7
    body += t(L, y, ">", TEAL, 700) + f'<rect class="cur" x="{L+22}" y="{y-14}" width="9" height="18" fill="{TEAL}"/>'
    css = ".cur{animation:bl 1.1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
    return svg(
        W, int(y + 36) if y + 36 > H else H, "Example evaluation in the terminal",
        "An illustrative evaluation of a fictional position: still open, gates, people, a score of 4.1 out of 5 with verdict Apply, a bar per dimension, the strongest reason in, the most likely reason out, one open CHECK and the next step.",
        body, css,
    )


for name, fn in [("hero.svg", hero), ("pipeline.svg", pipeline), ("fit.svg", fit), ("terminal.svg", terminal)]:
    (OUT / name).write_text(fn(), encoding="utf-8")
    print("wrote", OUT / name)
