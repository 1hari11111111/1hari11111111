"""Generate assets/contributions.svg from the public GitHub contribution calendar.
No token needed, no third-party server: runs inside your own GitHub Action."""
import datetime as dt
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_USER", "1hari11111111")
OUT = os.environ.get("OUT", "assets/contributions.svg")

req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

m = re.search(r"([\d,]+)\s*contributions\s*in the last year", html)
if not m:
    sys.exit("Could not read total contributions")
total = m.group(1)

counts = {}
for tid, text in re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>', html):
    n = re.match(r"(\d+) contribution", text)
    counts[tid] = int(n.group(1)) if n else 0

days = []
for tag in re.findall(r"<td[^>]*data-date=[^>]*>", html):
    date = re.search(r'data-date="([\d-]+)"', tag).group(1)
    level = int(re.search(r'data-level="(\d)"', tag).group(1))
    tid = re.search(r'id="(contribution-day-component-\d+-\d+)"', tag)
    days.append((dt.date.fromisoformat(date), level, counts.get(tid.group(1), 0) if tid else 0))
days.sort()
if not days:
    sys.exit("No contribution cells found")

first = days[0][0]
start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
weeks = ((days[-1][0] - start).days // 7) + 1

palette = ["#161b22", "#2d2a5e", "#4b43a8", "#6C63FF", "#00F5D4"]
cell, gap, left, top = 11, 3, 20, 70
width = left * 2 + weeks * (cell + gap)
height = top + 7 * (cell + gap) + 40

rects = []
for d, lvl, c in days:
    x = left + ((d - start).days // 7) * (cell + gap)
    y = top + ((d.weekday() + 1) % 7) * (cell + gap)
    rects.append(
        f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{palette[lvl]}">'
        f"<title>{c} contributions on {d}</title></rect>"
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="10" fill="#0d1117" stroke="#302b63"/>
<text x="{left}" y="32" fill="#6C63FF" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">{USER} contributions</text>
<text x="{left}" y="54" fill="#c9d1d9" font-family="Segoe UI,Arial,sans-serif" font-size="14"><tspan fill="#00F5D4" font-weight="700">{total}</tspan> contributions in the last year</text>
{chr(10).join(rects)}
<text x="{left}" y="{height - 14}" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="10">Updated {dt.date.today()}</text>
</svg>
"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(svg)
print(f"Wrote {OUT}: {total} contributions, {len(days)} days")
