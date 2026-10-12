"""Things, part 3: typing - a terminal that types lines, and can swap one word for another in place.

Why in-place: the swap is a real backspace-and-retype, with the caret moving through the same cells. Replacing
letters in place (not reflowing the line) requires the two words to have the SAME length; that is enforced.

Spec
----
  {"type": "typing", "dur": 13,
   "window_title": "zsh - manifesto",          (optional)
   "lines": [
     {"text": "Do not trust the Hype, trust your Hardware...",
      "prompt": "$",                           (optional, drawn at the start of the line)
      "emphasis": ["Hype"],                    (optional, words drawn in the emphasis colour)
      "swap": {"from": "ware", "to": "work"}}, (optional, from must occur exactly once, same length as to)
     {"text": "GET SHIT DONE.", "prompt": ">", "emphasis": ["GET"]}],
   "size": 30}                                 (optional font size)

Optional looks: "scanlines": true (fine dark lines over the text, as a CRT terminal), "glow": true (a soft
warm light in the centre of the window). Both default off.

Colours come from the theme and may be overridden with spec "colors":
  text_key (main text), accent (prompt), accent3 (emphasis and the new word), accent2 (the word being removed).

Static-first: every glyph's BASE opacity is its finished state (the removed letters are base 0, the new letters
base 1), so a renderer without SMIL shows the finished text, not overlapping letters.
"""
import sys

from diagram_common import FONT, F, T, esc, part

RUN = 0.84          # fraction of the loop used by typing; the rest holds the finished text
START = 0.04
CHAR, PAUSE_LINE, PAUSE_SWAP, DEL, RETYPE = 1.0, 3.0, 2.5, 1.0, 1.1   # raw relative times, scaled to RUN


def _lines(spec):
    out = []
    for i, raw in enumerate(spec["lines"]):
        ln = {"text": raw} if isinstance(raw, str) else dict(raw)
        if "text" not in ln:
            sys.exit(f"typing: lines[{i}] has no text")
        sw = ln.get("swap")
        if sw:
            frm, to = sw["from"], sw["to"]
            if len(frm) != len(to):
                sys.exit(f"typing: lines[{i}] swap '{frm}' -> '{to}' must have the same length (the swap is in place)")
            n = ln["text"].count(frm)
            if n != 1:
                sys.exit(f"typing: lines[{i}] swap 'from' ('{frm}') must occur exactly once in the line, found {n}")
            ln["_at"] = ln["text"].index(frm)
        out.append(ln)
    return out


def build_typing(spec, th, idp=""):
    """typing: a terminal types lines, and can swap one word for another in place.

    Fields: lines (required; each a string or {text, prompt, emphasis, swap:{from,to}}); dur
        (13); scanlines (false); glow (false); window_title; colors; size (30); width.
    Refuses: swap.from and swap.to of different lengths ('must have the same length'). swap.from
        not occurring exactly once in its line ('must occur exactly once'). A line with no text.
    Base state: removed letters have base opacity 0 and new letters base opacity 1, so the
        static fallback reads the finished sentence.
    Timing: each character gets a raw time; the whole schedule is scaled into the typing window,
        so the loop always ends with a hold.
    Alternatives: same-length swap, not reflow: a different length would move the rest of the
        line and read as a glitch.
    Breaks if changed: caret events must stay in time order; keyTimes must end at 1.
    Example: typing-manifesto.json (see references/learned/typing.md)   Tests:
        tests/test_type_coverage.py.
    """
    dur = float(spec.get("dur", 13))
    lines = _lines(spec)
    FS = float(spec.get("size", 30))
    CW = FS * 0.6
    X0 = 112.0
    Y0, GAP = 118.0, FS * 2.8
    maxlen = max(len(l["text"]) + len(l.get("prompt", "")) + 2 for l in lines)
    W = int(spec.get("width", max(900, X0 + maxlen * CW + 90)))
    H = int(Y0 + (len(lines) - 1) * GAP + 96)
    col = {
        "text": spec.get("colors", {}).get("text_key", th["text_key"]),
        "prompt": spec.get("colors", {}).get("accent", th["accent"]),
        "emph": spec.get("colors", {}).get("accent3", th["accent3"]),
        "from": spec.get("colors", {}).get("accent2", th["accent2"]),
    }
    mono = FONT
    # ---- raw schedule: relative times, then scaled to [START, START + RUN]
    raw = 0.0
    glyphs = []      # dict(i, x, y, ch, color, base, show, hide, kind)
    caret = []       # (raw_time, x, y)
    sb_raw = []      # (label, t0, t1)
    for li, ln in enumerate(lines):
        y = Y0 + li * GAP
        text = ln["text"]
        emph = set()
        for w in ln.get("emphasis", []):
            k = text.find(w)
            while k != -1:
                emph.update(range(k, k + len(w)))
                k = text.find(w, k + 1)
        sw = ln.get("swap")
        t_line0 = raw
        for j, c in enumerate(text):
            raw += CHAR
            if c == " ":
                caret.append((raw, X0 + (j + 1) * CW, y))
                continue
            in_swap = sw and ln["_at"] <= j < ln["_at"] + len(sw["from"])
            color = col["from"] if in_swap else (col["emph"] if j in emph else col["text"])
            g = dict(x=X0 + j * CW, y=y, ch=c, color=color, base=0 if in_swap else 1, show=raw, hide=None, line=li)
            glyphs.append(g)
            caret.append((raw, X0 + (j + 1) * CW, y))
        if sw:
            raw += PAUSE_SWAP
            k0 = ln["_at"]
            nfrom = len(sw["from"])
            for k in range(nfrom - 1, -1, -1):          # backspace last to first
                raw += DEL
                idx = k0 + k
                for g in glyphs:
                    if g["line"] == li and g["x"] == X0 + idx * CW and g["base"] == 0 and g["hide"] is None:
                        g["hide"] = raw
                caret.append((raw, X0 + idx * CW, y))
            for k, c in enumerate(sw["to"]):             # retype the new word in the same cells
                raw += RETYPE
                idx = k0 + k
                glyphs.append(dict(x=X0 + idx * CW, y=y, ch=c, color=col["emph"], base=1, show=raw, hide=None, line=li))
                caret.append((raw, X0 + (idx + 1) * CW, y))
        raw += PAUSE_LINE
        sb_raw.append((f"line {li + 1}" + (" + swap" if sw else ""), t_line0, raw))
    total = max(raw, 1e-9)
    scale = RUN / total

    def T_(r):
        return START + r * scale

    # ---- the body: window chrome, glyphs, caret
    body = []
    if spec.get("glow"):
        body.append(f'<defs><radialGradient id="{idp}tglow" cx="50%" cy="45%" r="62%"><stop offset="0" stop-color="{th["accent2"]}" stop-opacity="0.16"/>'
                    f'<stop offset="1" stop-color="{th["bg"]}" stop-opacity="0"/></radialGradient></defs>')
        body.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#{idp}tglow)"/>')
    body.append(f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" rx="16" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.4"/>')
    body.append(f'<path d="M20,56 V36 a16,16 0 0 1 16,-16 H{W - 36} a16,16 0 0 1 16,16 V56 Z" fill="{th["surface_key"]}"/>')
    for k, cc in enumerate(("#B5402A", "#B08D57", "#5C4A3B")):
        body.append(f'<circle cx="{50 + 22 * k}" cy="38" r="6" fill="{cc}"/>')
    if spec.get("window_title"):
        body.append(f'<text x="{W / 2}" y="43" text-anchor="middle" font-family="{mono}" font-size="13" fill="{th["muted"]}" letter-spacing="1">{esc(spec["window_title"])}</text>')
    # prompts (always visible; they are part of the finished graphic)
    for li, ln in enumerate(lines):
        if ln.get("prompt"):
            body.append(f'<text x="{F(X0 - 2 * CW)}" y="{F(Y0 + li * GAP)}" font-family="{mono}" font-size="{F(FS)}" font-weight="700" fill="{col["prompt"]}">{esc(ln["prompt"])}</text>')
    for g in glyphs:
        if g["base"] == 0:
            vals, keys = "0;1;0", f"0;{T(T_(g['show']))};{T(T_(g['hide']))}"
        else:
            vals, keys = "0;1", f"0;{T(T_(g['show']))}"
        weight = "700" if g["color"] == col["emph"] else "500"
        body.append(f'<text x="{F(g["x"])}" y="{F(g["y"])}" font-family="{mono}" font-size="{F(FS)}" font-weight="{weight}" fill="{g["color"]}" opacity="{g["base"]}">'
                    f'{esc(g["ch"])}<animate attributeName="opacity" calcMode="discrete" values="{vals}" keyTimes="{keys}" dur="{dur:g}s" repeatCount="indefinite"/></text>')
    if spec.get("scanlines"):
        body.append("".join(f'<rect x="20" y="{y}" width="{W - 40}" height="1" fill="#000" opacity="0.18"/>' for y in range(60, H - 20, 4)))
    # caret: one rect moved along the path of (time, x, y) events; its base position is the finished end
    path = [(0.0, X0, Y0)] + [(T_(r), x, y) for r, x, y in caret]
    path.sort(key=lambda p: p[0])
    dedup = []
    for p in path:
        if dedup and abs(dedup[-1][0] - p[0]) < 1e-6:
            dedup[-1] = p
        else:
            dedup.append(p)
    kt = ";".join(T(p[0]) for p in dedup) + ";1"
    vals = ";".join(f"{p[1]:.1f} {p[2]:.1f}" for p in dedup) + f";{dedup[-1][1]:.1f} {dedup[-1][2]:.1f}"
    ex, ey = dedup[-1][1], dedup[-1][2]
    body.append(f'<g transform="translate({F(ex)} {F(ey)})"><animateTransform attributeName="transform" type="translate" calcMode="discrete" additive="replace" '
                f'keyTimes="{kt}" values="{vals}" dur="{dur:g}s" repeatCount="indefinite"/>'
                f'<rect x="0" y="{F(-FS * 0.82)}" width="{F(CW * 0.9)}" height="{F(FS * 1.02)}" fill="{col["text"]}">'
                f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5001;1" dur="0.9s" repeatCount="indefinite"/></rect></g>')
    sb = [f"type=typing  lines={len(lines)}  loop={dur:g}s  swap-in-place on {sum(1 for l in lines if l.get('swap'))} line(s)"]
    sb += [f"at {T_(a):.3f}..{T_(b):.3f} {lbl}" for lbl, a, b in sb_raw]
    return part("".join(body), W, H, sb, False,
                "Typing: " + " / ".join(l["text"] for l in lines))


TYPING = {"typing": build_typing}
