"""Plot the eval scores of each skill as bars in one self-contained HTML file.

Reads the results tables of the eval findings READMEs (`plugins/*/evals/README.md`,
the tables written with `scripts/eval_tables.py`) and writes one bar chart per
skill. A bar is one model with or without the plugin; its height is the mean
score over all cases of the suite (negative cases included), and the bars are
sorted in decreasing order from left to right. The score is written above
each bar and the model logo sits inside its top; below it, the model name and
With/Without.

Model logos are read from `asset/` (or `asset/models/`) as <family>.(svg|png|jpg|webp), with
<family> the first word of the model label in lower case (`Opus 5.5` -> `opus`,
`Gemma 4 31B` -> `gemma`); a coloured initial is drawn when a file is missing.
Images are embedded in the HTML, which needs no network.

    python scripts/eval_plot.py                      # all plugins/*/evals/README.md
    python scripts/eval_plot.py README.md ... -o out.html
"""

import argparse
import base64
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
FALLBACK = ["#000000", "#404040", "#737373", "#a3a3a3"]


def num(cell):
    """'**+0.33**', '−0.17', '0.86' -> float."""
    return float(cell.strip("* ").replace("−", "-"))


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_readme(path):
    """-> list of (skill, [(model, with_score, without_score), ...]) from the
    results table (the one with Δ columns) under each `## `skill`` heading."""
    skills, skill, i = [], None, 0
    lines = path.read_text().splitlines()
    while i < len(lines):
        line = lines[i]
        m = re.match(r"## `([^`]+)`", line)
        if m:
            skill = m.group(1)
        elif skill and re.match(r"\|\s*Case\s*\|", line) and "Δ" in line:
            header = cells(line)[1:]
            models = [h[: -len(" with")] for h in header if h.endswith(" with")]
            rows = []
            i += 2  # skip the separator
            while i < len(lines) and lines[i].startswith("|"):
                c = cells(lines[i])
                if c[0].startswith("`"):  # case rows only, not the Mean rows
                    rows.append(c[1:])
                i += 1
            if rows:
                bars = []
                for k, model in enumerate(models):
                    w = [num(r[3 * k]) for r in rows]
                    wo = [num(r[3 * k + 1]) for r in rows]
                    bars.append((model, sum(w) / len(w), sum(wo) / len(wo)))
                skills.append((skill, bars, len(rows)))
            skill = None
            continue
        i += 1
    return skills


def data_uri(path):
    return f"data:{MIME[path.suffix]};base64," + base64.b64encode(path.read_bytes()).decode()


def find_logo(model):
    family = model.split()[0].lower()
    for d in ("models", ""):
        for ext in MIME:
            p = ROOT / "asset" / d / f"{family}{ext}"
            if p.exists():
                return data_uri(p)
    print(f"warning: no logo asset/models/{family}.(svg|png|jpg|webp)", file=sys.stderr)
    return None


# geometry of one chart (SVG user units)
SLOT, BAR, BASE, HMAX, PAD = 112, 84, 330, 230, 34
LOGO = 22


def chart(bars, logos, colors):
    bars = sorted(
        [(m, arm, s) for m, w, wo in bars for arm, s in (("With", w), ("Without", wo))],
        key=lambda b: -b[2],
    )
    width, top = PAD + SLOT * len(bars), BASE - HMAX - 30
    height = BASE + 12 - top
    out = [f'<svg viewBox="0 {top} {width} {height}" role="img" xmlns="http://www.w3.org/2000/svg">']
    def metal(gid, stops):
        st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
        return f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">{st}</linearGradient>'

    out.append(
        "<defs>"
        + metal("m-with", [(0, "#0a8a62"), (0.18, "#11ba83"), (0.38, "#7ff0c8"), (0.52, "#2fd09b"), (0.78, "#0fae7a"), (1, "#087a56")])
        + metal("m-without", [(0, "#9a9a9a"), (0.18, "#cfcfcf"), (0.38, "#fafafa"), (0.52, "#dcdcdc"), (0.78, "#bdbdbd"), (1, "#8a8a8a")])
        + '<linearGradient id="m-shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/>'
        '<stop offset=".08" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>'
        "</defs>"
    )
    for t in (0, 0.25, 0.5, 0.75, 1):
        y = BASE - t * HMAX
        out.append(f'<line class="grid" x1="{PAD}" x2="{width}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="tick" x="2" y="{y - 3:.1f}">{t:.2f}</text>')
    for k, (model, arm, score) in enumerate(bars):
        cx = PAD + SLOT * k + SLOT / 2
        h = score * HMAX
        y = BASE - h
        cls = "with" if arm == "With" else "without"
        r, bx = min(10, h / 2), cx - BAR / 2
        path = (f"M{bx:.1f},{BASE} V{y + r:.1f} Q{bx:.1f},{y:.1f} {bx + r:.1f},{y:.1f} H{bx + BAR - r:.1f} "
                f"Q{bx + BAR:.1f},{y:.1f} {bx + BAR:.1f},{y + r:.1f} V{BASE} Z")
        out.append(f'<path d="{path}" class="bar" fill="url(#m-{cls})">'
                   f"<title>{escape(model)} {arm.lower()}: {score:.3f}</title></path>")
        out.append(f'<path d="{path}" fill="url(#m-shade)" pointer-events="none"/>')
        out.append(f'<text class="val" x="{cx:.1f}" y="{y - 6:.1f}" text-anchor="middle">{score:.2f}</text>')
        s = LOGO  # model logo inside the bar top, name and With/Without just below
        if h >= s + 52:
            ly = y + 8
            if logos[model]:
                out.append(f'<image href="{logos[model]}" x="{cx - s / 2:.1f}" y="{ly:.1f}" width="{s}" height="{s}"/>')
            else:
                out.append(f'<circle cx="{cx:.1f}" cy="{ly + s / 2:.1f}" r="{s / 2}" fill="{colors[model]}"/>')
                out.append(f'<text class="initial" x="{cx:.1f}" y="{ly + s / 2 + 4:.1f}" text-anchor="middle">{escape(model[0])}</text>')
            out.append(f'<text class="name {cls}" x="{cx:.1f}" y="{ly + s + 15:.1f}" text-anchor="middle">{escape(model)}</text>')
            out.append(f'<text class="arm {cls}" x="{cx:.1f}" y="{ly + s + 29:.1f}" text-anchor="middle">{arm}</text>')
    out.append("</svg>")
    return "\n".join(out)


CSS = """
:root{--bg:#f5f5f5;--card:#fff;--fg:#000;--muted:#737373;--grid:#ececec;--with:#11ba83;--without:#c8c8c8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Inter","Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:1060px;margin:0 auto;padding:48px 16px 64px}
h1{font-size:2rem;font-weight:700;letter-spacing:-.02em;margin:0 0 6px}
p.sub{color:var(--muted);margin:0 0 20px;font-size:1rem}
.legend{display:flex;gap:20px;margin:0 0 28px;font-size:.875rem;color:var(--muted)}
.legend i{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px}
.legend i{background:linear-gradient(90deg,#9a9a9a,#fafafa 40%,#8a8a8a);opacity:.8}.legend .with i{background:linear-gradient(90deg,#0a8a62,#7ff0c8 40%,#087a56)}
section{background:var(--card);border-radius:18px;padding:24px 24px 12px;margin-bottom:24px;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.05)}
h2{font-size:1.1rem;font-weight:650;margin:0}
h2 code{font:600 1.05rem ui-monospace,SFMono-Regular,Menlo,monospace}
h2 small{color:var(--muted);font-weight:400;font-size:.85rem;margin-left:6px}
section p{color:var(--muted);margin:2px 0 4px;font-size:.85rem}
.scroll{overflow-x:auto}svg{width:100%;min-width:560px;height:auto;display:block}
.bar{fill-opacity:.5}
.grid{stroke:var(--grid)}.axis{stroke:#d4d4d4}
.tick{fill:var(--muted);font-size:10px}.val{fill:var(--fg);font-size:14px;font-weight:650}
.name{font-size:11px;font-weight:600}.arm{font-size:10.5px}
.name,.arm{fill:#000}.arm{opacity:.85}
.initial{fill:#fff;font-size:12px;font-weight:700}
"""


def render(skills):
    colors, logos = {}, {}
    for _, _, bars, _ in skills:
        for model, *_ in bars:
            if model not in logos:
                logos[model] = find_logo(model)
                colors[model] = FALLBACK[len(colors) % len(FALLBACK)]
    body = []
    for plugin, skill, bars, ncases in skills:
        body.append(
            f"<section><h2><code>{escape(skill)}</code> <small>({escape(plugin)} plugin)</small></h2>"
            f"<p>Mean score over {ncases} cases, 0–1 scale.</p>"
            f'<div class="scroll">{chart(bars, logos, colors)}</div></section>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Eval scores</title><style>{CSS}</style></head><body><main>"
        "<h1>Eval scores per skill</h1>"
        '<p class="sub">Each bar is one agent model with or without the plugin, sorted by mean score.</p>'
        '<div class="legend"><span class="with"><i></i>With plugin</span>'
        '<span class="without"><i></i>Without plugin</span></div>'
        + "\n".join(body)
        + "</main></body></html>"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("readmes", nargs="*", type=Path, help="default: plugins/*/evals/README.md")
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "web" / "index.html")
    a = ap.parse_args()
    readmes = a.readmes or sorted(ROOT.glob("plugins/*/evals/README.md"))
    skills = []
    for r in readmes:
        plugin = r.resolve().parent.parent.name
        skills += [(plugin, s, b, n) for s, b, n in parse_readme(r)]
    if not skills:
        sys.exit("no results tables found")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(render(skills))
    print(f"wrote {a.output} ({len(skills)} skills)")


if __name__ == "__main__":
    main()
