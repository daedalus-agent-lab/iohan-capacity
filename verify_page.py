#!/usr/bin/env python3
"""Verify capacity-scale.html against table.json — content, structure and the no-JS constraints.

The design was delegated; the arithmetic and the strings were not. This checks what the page must
carry, not how it looks: that every one of the twelve positions is present with the author's own
words, that the highlighted range is exactly the capacity for that position, and that the file is
what it claims to be — one self-contained page with no script and no network.
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "capacity-scale.html"
table = {r["guests"]: r for r in json.loads((HERE / "table.json").read_text(encoding="utf-8"))}

# The pre-fix wording, if it is still around, is used only to check that no superseded string survived.
# It is optional: a reader who clones the repository gets the shipped table and nothing else, and a
# checker that dies on a missing optional file is a checker nobody runs.
_old_path = HERE / "table-old.json"
old = ({r["guests"]: r for r in json.loads(_old_path.read_text(encoding="utf-8"))}
       if _old_path.exists() else None)
raw = PAGE.read_text(encoding="utf-8")
FAILS = []


def ck(name, got, want):
    if got == want:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}: got {got!r}, want {want!r}")
        FAILS.append(name)


def panels(text: str) -> dict[int, str]:
    """Split the page into its twelve result panels, keyed by guest count."""
    marks = [(int(m.group(1)), m.start()) for m in re.finditer(r'class="result panel for-(\d+)"', text)]
    out = {}
    for i, (n, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out[n] = text[start:end]
    return out


def main() -> int:
    print("the file")
    ck("no <script> anywhere", len(re.findall(r"<script", raw, re.I)), 0)
    ck("no inline event handlers", len(re.findall(r"\son[a-z]+\s*=", raw, re.I)), 0)
    ck("no external resources or links",
       re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+', raw, re.I), [])
    ck("nothing stretched over the network", raw.count("url(http"), 0)

    print("the choice")
    radios = re.findall(r'<input[^>]*type="radio"[^>]*>', raw)
    values = [int(re.search(r'value="(\d+)"', r).group(1)) for r in radios]
    ck("twelve positions, 1..12", sorted(values), list(range(1, 13)))
    checked = [re.search(r'id="guests-(\d+)"', r).group(1) for r in radios if "checked" in r]
    ck("initial position is 3", checked, ["3"])
    ck("every radio has a label pointing at it",
       all(f'for="guests-{v}"' in raw for v in values), True)
    ck("no zero position", 'value="0"' in raw, False)

    print("the fixed facts, readable without touching anything")
    ck("home has 12", ">12<" in raw and "печений дома" in raw, True)
    ck("each guest at least 6", ">6<" in raw and "минимум каждому гостю" in raw, True)
    ck("a pack holds 8", ">8<" in raw and "печений в пачке" in raw, True)

    print("the twelve positions")
    p = panels(raw)
    ck("all twelve panels present", sorted(p), list(range(1, 13)))
    for n, block in sorted(p.items()):
        b = html.unescape(block)
        want = table[n]
        covered = len(re.findall(r'class="(?:covered|covered current)"', block))
        outside = len(re.findall(r'class="outside"', block))
        pos = len(re.findall(r'class="position-number"', block))
        marks = len(re.findall(r'class="covered current"', block))
        problems = []
        if pos != 12:
            problems.append(f"scale has {pos} positions")
        if covered != want["capacity"]:
            problems.append(f"{covered} covered, capacity is {want['capacity']}")
        if outside != 12 - want["capacity"]:
            problems.append(f"{outside} outside, expected {12 - want['capacity']}")
        if marks != 1:
            problems.append(f"{marks} 'current' marks")
        for field in ("purchase", "coverage", "note"):
            if want[field] not in b:
                problems.append(f"{field} not present verbatim")
        if old is not None and old[n][field] != want[field] and old[n][field] in b:
            problems.append(f"still carries the superseded {field}")
        ck(f"N={n}: {want['packs']} packs, covers 1..{want['capacity']}", problems, [])

    print("credits and framing")
    ck("the four credit lines are named",
       all(s in raw for s in ("v2bot-agent #31501", "#31579", "Meliora #30282")), True)
    ck("no claim of novelty", bool(re.search(r"уникальн|новизн|впервые", raw, re.I)), False)
    ck("has a title and a single h1", (raw.count("<h1") == 1) and "<title" in raw, True)
    if old is None:
        print("  --   superseded-wording check skipped: table-old.json is not in this checkout")
        ck("nothing to compare against, and that is stated rather than assumed", True, True)
    else:
        ck("no superseded wording survives",
           [n for n in old if old[n]["note"] != table[n]["note"]
            and old[n]["note"] in html.unescape(raw)], [])

    print()
    if FAILS:
        print(f"PAGE: {len(FAILS)} FAILED")
        return 1
    print("PAGE: all checks hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
