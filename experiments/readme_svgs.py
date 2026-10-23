"""Animated SVGs for the README: the opening lily, how the system fits together, and the roadmap.

GitHub runs no JavaScript in a README, but it does play SVG animation (SMIL), so the website's motion is
redrawn here as plain SVG. Writes docs/img/hero.svg, docs/img/pipeline.svg and docs/img/roadmap.svg.
The README shows docs/banner.png instead of the hero to readers who ask for reduced motion."""
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMG = os.path.join(ROOT, "docs", "img"); os.makedirs(IMG, exist_ok=True)

ICE, BG, PAPER, AUB, INK, MUT, DIM = "#DDE3E8", "#E6EAED", "#F2F4F6", "#3A0F34", "#2B0A27", "#66525F", "#97899A"
MARI, MARI2, OK = "#EAAA00", "#B98600", "#2F7A52"
SANS = "'Inter Tight','Inter','Helvetica Neue',Helvetica,Arial,sans-serif"
SERIF = "'Cormorant Garamond',Georgia,'Times New Roman',serif"
MONO = "'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace"
EASE = 'calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1"'


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def petal(L, W, C):
    """The website's petal: a closed double Bezier pointing up from the origin."""
    return (f"M0 0C{f(W)} {f(-L * .22)} {f(W * .95 + C * .4)} {f(-L * .72)} {f(C)} {f(-L)}"
            f"C{f(-W * .9 + C * .4)} {f(-L * .74)} {f(-W * .7)} {f(-L * .24)} 0 0Z")


def flower(cx, cy, S, begin, blur_extra, uid):
    """Eight blurred petals that open out of a bud, then sway; stamens and a stem."""
    ang = [-158, -116, -74, -34, 6, 46, 92, 132]
    blurs = [9, 2, .6, 5, 1, .8, 3, 12]
    out = [f'<g id="{uid}">']
    sx = cx - S * 1.1
    out.append(f'<path d="M{f(cx)} {f(cy)}C{f(cx - S * .15)} {f(cy + S * .8)} {f(cx - S * .7)} {f(cy + S * 1.2)} {f(sx)} {f(cy + S * 2.4)}" '
               f'stroke="url(#stem)" stroke-width="{f(S * .035)}" fill="none" stroke-linecap="round" filter="url(#b{2 + blur_extra})" opacity="0">'
               f'<animate attributeName="opacity" to="1" begin="{begin}s" dur="1.2s" fill="freeze"/></path>')
    for i, a in enumerate(ang):
        L = S * (i % 2 and .92 or 1.06); C = S * (-.16 if i < 4 else .16); W = S * .2
        b = min(12, round(blurs[i]) + blur_extra)
        a0, a1 = a * .35, a + math.sin(i * 1.7) * 3
        sway = 2.5 + (i % 3)
        out.append(f'<g transform="translate({f(cx)} {f(cy)})"><g>'
                   f'<animateTransform attributeName="transform" type="rotate" values="{f(a0)};{f(a1)}" begin="{begin}s" dur="2.6s" fill="freeze" {EASE}/>'
                   f'<animateTransform attributeName="transform" type="rotate" values="0;{sway};0;{-sway};0" begin="{begin + 2.6}s" dur="{7 + i % 4}s" repeatCount="indefinite" additive="sum"/>'
                   f'<path d="{petal(L, W, C)}" fill="url(#petal)" filter="url(#b{b})" opacity="0" transform="scale(.55)">'
                   f'<animate attributeName="opacity" to=".92" begin="{begin}s" dur="1.4s" fill="freeze"/>'
                   f'<animateTransform attributeName="transform" type="scale" values=".55;1" begin="{begin}s" dur="2.6s" fill="freeze" {EASE}/></path></g></g>')
    for k in range(6):
        a = math.radians(-120 + k * 14); r = S * (.5 + .1 * (k % 3))
        x2, y2 = cx + math.cos(a) * r, cy + math.sin(a) * r
        qx, qy = cx + math.cos(a) * r * .5 + 6, cy + math.sin(a) * r * .5
        out.append(f'<g opacity="0" filter="url(#b{1 + blur_extra})"><animate attributeName="opacity" to="1" begin="{begin + 1.4 + k * .08}s" dur="1s" fill="freeze"/>'
                   f'<path d="M{f(cx)} {f(cy)}Q{f(qx)} {f(qy)} {f(x2)} {f(y2)}" stroke="{AUB}" stroke-opacity=".75" stroke-width="1.6" fill="none"/>'
                   f'<ellipse cx="{f(x2)}" cy="{f(y2)}" rx="5" ry="2.6" fill="{MARI}" transform="rotate({f(math.degrees(a))} {f(x2)} {f(y2)})"/></g>')
    out.append("</g>")
    return "".join(out)


def pollen(n, x0, x1, y0, rise, seed=3):
    import random
    rnd = random.Random(seed); out = []
    for i in range(n):
        x = rnd.uniform(x0, x1); r = rnd.uniform(3, 8); d = rnd.uniform(6, 11); b = rnd.uniform(2.5, 9)
        out.append(f'<circle cx="{f(x)}" cy="{f(y0)}" r="{f(r)}" fill="url(#dot)" opacity="0">'
                   f'<animate attributeName="cy" values="{f(y0)};{f(y0 - rise * rnd.uniform(.6, 1))}" begin="{f(b)}s" dur="{f(d)}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="cx" values="{f(x)};{f(x + rnd.uniform(-24, 24))};{f(x)}" begin="{f(b)}s" dur="{f(d)}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;.85;0" begin="{f(b)}s" dur="{f(d)}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


def blur_filters(xs):
    return "".join(f'<filter id="b{i}" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="{i}"/></filter>' for i in xs)


def cap(x, y, text, anchor="start", fill=AUB, size=12, ls=4.2, op=1):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" opacity="{op}" '
            f'style="font:600 {size}px {SANS};letter-spacing:{ls}px">{text}</text>')


def hero():
    W, H = 1600, 560
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="DairyGuard keeps the clock. Milk keeps its own clock; we read it.">',
         "<defs>",
         '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9ECEE"/><stop offset="1" stop-color="#DFE4E8"/></linearGradient>',
         '<radialGradient id="glow" cx=".72" cy=".42" r=".42"><stop offset="0" stop-color="#EAAA00" stop-opacity=".2"/><stop offset="1" stop-color="#EAAA00" stop-opacity="0"/></radialGradient>',
         '<linearGradient id="petal" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#1c0519"/><stop offset=".28" stop-color="#3A0F34"/>'
         '<stop offset=".5" stop-color="#7a2a52"/><stop offset=".66" stop-color="#EAAA00"/><stop offset=".86" stop-color="#F7D57A"/><stop offset="1" stop-color="#FAF0DC" stop-opacity=".9"/></linearGradient>',
         '<linearGradient id="stem" x1="0" y1="0" x2="-.4" y2="1"><stop offset="0" stop-color="#EAAA00"/><stop offset=".35" stop-color="#3A0F34"/><stop offset="1" stop-color="#3A0F34" stop-opacity=".3"/></linearGradient>',
         '<radialGradient id="dot"><stop offset="0" stop-color="#F7D57A"/><stop offset=".35" stop-color="#F7D57A" stop-opacity=".55"/><stop offset="1" stop-color="#F7D57A" stop-opacity="0"/></radialGradient>',
         blur_filters(range(1, 15)),
         '<filter id="w0" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="60 0"><animate attributeName="stdDeviation" values="60 0;3 0" begin=".2s" dur="1.6s" fill="freeze" ' + EASE + '/></feGaussianBlur></filter>',
         '<filter id="w1" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="60 0"><animate attributeName="stdDeviation" values="60 0;5 0" begin=".55s" dur="1.6s" fill="freeze" ' + EASE + '/></feGaussianBlur></filter>',
         "</defs>",
         f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#glow)"/>']
    s += [f'<line x1="{f(56 + i * (W - 112) / 8)}" x2="{f(56 + i * (W - 112) / 8)}" y1="0" y2="{H}" stroke="{AUB}" stroke-opacity=".07"/>' for i in range(9)]
    s.append(flower(1180, 250, 330, .1, 0, "lily"))
    s.append(flower(842, 500, 175, .5, 3, "bud"))
    s.append(pollen(14, 980, 1380, 300, 260))
    s.append(cap(56, 55, "DAIRYGUARD · OPEN RESEARCH")); s.append(cap(W - 56, 55, "PYTHON · C · JAVASCRIPT", "end"))
    for i, (txt, x, y, tl, b) in enumerate([("DairyGuard", 50, 248, 640, .2), ("keeps the clock.", 128, 352, 905, .55)]):
        s.append(f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{b}s" dur="1.2s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="220 0;0 0" begin="{b}s" dur="1.6s" fill="freeze" {EASE}/>'
                 f'<text x="{x}" y="{y}" textLength="{tl}" lengthAdjust="spacingAndGlyphs" fill="{AUB}" filter="url(#w{i})" '
                 f'style="font:900 128px {SANS};letter-spacing:-6px">{txt}</text></g>')
    s.append(f'<g opacity="0"><animate attributeName="opacity" to="1" begin="1.5s" dur="1.4s" fill="freeze"/>'
             f'<text x="56" y="477" fill="{AUB}" style="font:italic 500 24px {SERIF}">Milk keeps its own clock. We read it.</text>'
             f'<text x="56" y="511" fill="{AUB}" style="font:600 15px {SANS}">An open cold-chain monitor: data, models, firmware and a browser app.</text></g>')
    s.append(f'<g fill="{AUB}"><text x="{W - 56}" y="490" text-anchor="end" style="font:700 11px {SANS};letter-spacing:2px">01</text>'
             + "".join(f'<rect x="{W - 56 - (22 if k == 0 else 10)}" y="{498 + k * 6}" width="{22 if k == 0 else 10}" height="1.5" opacity="{1 if k == 0 else .4}"/>' for k in range(4)) + "</g>")
    s.append("</svg>")
    return "".join(s)


def pipeline():
    W, H = 1600, 520
    boxes = {  # x, y, title, three lines, highlight
        "D": (40, 70, "1 · Data", ["373 ComBase milk records", "published experiments", "every value sourced"], False),
        "M": (430, 70, "2 · Models", ["square-root growth law", "Gompertz shelf life", "Baranyi reference"], False),
        "E": (820, 70, "3 · Monitor", ["shelf life used", "chance limit crossed", "hours left · verdict"], True),
        "P": (1210, 70, "5 · Runs on", ["Python package + CLI", "C firmware for ESP32", "browser app"], False),
        "S": (625, 330, "4 · Evaluation", ["240,000 simulated trips", "AUC · paired bootstrap", "calibration"], False),
    }
    bw, bh = 350, 150
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="How DairyGuard fits together: data feeds the models, the models feed the monitor, the monitor runs in Python, firmware and the browser, and a simulator evaluates it.">',
         '<defs><radialGradient id="pulse"><stop offset="0" stop-color="#F7D57A"/><stop offset=".45" stop-color="#EAAA00"/><stop offset="1" stop-color="#EAAA00" stop-opacity="0"/></radialGradient>'
         '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#97899A"/></marker></defs>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{BG}"/>']
    mid = lambda k: (boxes[k][0] + bw / 2, boxes[k][1] + bh / 2)
    paths = [("D", f"M{40 + bw} 145H{430 - 6}"), ("M", f"M{430 + bw} 145H{820 - 6}"), ("E", f"M{820 + bw} 145H{1210 - 6}"),
             ("M2", f"M{605} {70 + bh}C605 290 700 270 {740} {330 - 6}"), ("E2", f"M{995} {70 + bh}C995 290 900 270 {860} {330 - 6}")]
    for i, (k, d) in enumerate(paths):
        s.append(f'<path id="p{k}" d="{d}" stroke="{DIM}" stroke-width="1.6" fill="none" marker-end="url(#ah)" stroke-dasharray="600" stroke-dashoffset="600">'
                 f'<animate attributeName="stroke-dashoffset" to="0" begin="{.9 + i * .25}s" dur="1s" fill="freeze"/></path>')
    for i, (k, x) in enumerate(boxes.items()):
        x0, y0, title, lines, hot = x
        fill, stroke = ("#F6E7BC", MARI2) if hot else (PAPER, "rgba(58,15,52,.18)")
        s.append(f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{i * .18}s" dur=".8s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 24;0 0" begin="{i * .18}s" dur="1s" fill="freeze" {EASE}/>'
                 f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bh}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
                 f'<text x="{x0 + 26}" y="{y0 + 44}" fill="{INK}" style="font:800 25px {SANS};letter-spacing:-.5px">{title}</text>'
                 + "".join(f'<text x="{x0 + 26}" y="{y0 + 78 + j * 24}" fill="{MUT}" style="font:500 15px {SANS}">{t}</text>' for j, t in enumerate(lines))
                 + "</g>")
        if hot:
            s.append(f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bh}" rx="20" fill="none" stroke="{MARI}" stroke-width="2" opacity="0">'
                     f'<animate attributeName="opacity" values="0;.9;0" begin="2.4s" dur="2.4s" repeatCount="indefinite"/></rect>')
    for i, (k, _) in enumerate(paths):
        for j in range(2):
            s.append(f'<circle r="9" fill="url(#pulse)" opacity="0"><animateMotion dur="2.4s" begin="{2.2 + i * .35 + j * 1.2}s" repeatCount="indefinite"><mpath href="#p{k}"/></animateMotion>'
                     f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.8;1" dur="2.4s" begin="{2.2 + i * .35 + j * 1.2}s" repeatCount="indefinite"/></circle>')
    s.append(cap(40, 40, "HOW IT WORKS", fill=MUT, size=11))
    s.append(f'<text x="1560" y="{H - 34}" text-anchor="end" fill="{MUT}" style="font:500 13px {MONO}">every reading: advance the clock · carry 80 batches · decide</text>')
    s.append("</svg>")
    return "".join(s)


def roadmap():
    W, H = 1600, 330
    stops = [("OCT 2026", "DairyGuard Kinetic", "package, firmware, app, book", "DONE"),
             ("OCT 2026", "Real-data checks", "20 unseen Listeria studies", "DONE"),
             ("NOV – DEC 2026", "Curves and protocol", "ComBase curves, lab protocol", "NOW"),
             ("JAN – FEB 2027", "First lab measurements", "steady and shifting temperatures", "NEXT"),
             ("THEN", "DairyGuard Batch", "built to the WP-02 blueprint", "PLANNED"),
             ("THEN", "Peer review", "a journal paper on lab results", "PLANNED")]
    x0, x1, y = 120, W - 120, 120
    xs = [x0 + i * (x1 - x0) / (len(stops) - 1) for i in range(len(stops))]
    now = xs[2]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Roadmap: DairyGuard Kinetic and real-data checks done in October 2026; curves and lab protocol now; first lab counts January to February 2027; then DairyGuard Batch and peer review.">',
         f'<defs><linearGradient id="lit" gradientUnits="userSpaceOnUse" x1="{x0}" x2="{f(now)}" y1="0" y2="0"><stop offset="0" stop-color="{AUB}"/><stop offset="1" stop-color="{MARI}"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{BG}"/>', cap(40, 44, "ROADMAP", fill=MUT, size=11),
         f'<line x1="{x0}" x2="{x1}" y1="{y}" y2="{y}" stroke="{AUB}" stroke-opacity=".14" stroke-width="2"/>',
         f'<line x1="{x0}" x2="{x0}" y1="{y}" y2="{y}" stroke="url(#lit)" stroke-width="4" stroke-linecap="round"><animate attributeName="x2" to="{f(now)}" begin=".3s" dur="2.4s" fill="freeze" {EASE}/></line>']
    for i, (when, title, sub, st) in enumerate(stops):
        x = xs[i]; on = i <= 2; t = .3 + 2.4 * (x - x0) / (now - x0) * .8 if on else 0
        dot = (f'<circle cx="{f(x)}" cy="{y}" r="8" fill="{BG}" stroke="{DIM}" stroke-width="1.6">'
               + (f'<animate attributeName="fill" to="{MARI}" begin="{f(t)}s" dur=".4s" fill="freeze"/><animate attributeName="stroke" to="{MARI}" begin="{f(t)}s" dur=".4s" fill="freeze"/>' if on else "")
               + "</circle>")
        if st == "NOW":
            dot = (f'<circle cx="{f(x)}" cy="{y}" r="8" fill="{MARI}" opacity="0"><animate attributeName="r" values="8;22" begin="{f(t + .4)}s" dur="1.8s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values=".45;0" begin="{f(t + .4)}s" dur="1.8s" repeatCount="indefinite"/></circle>') + dot
        pill = {"DONE": (OK, "none"), "NOW": (AUB, MARI), "NEXT": (MUT, "none"), "PLANNED": (DIM, "none")}[st]
        pw = 13 + len(st) * 9.5
        op = 1 if on or st == "NEXT" else .5
        s.append(f'<g opacity="0"><animate attributeName="opacity" to="{op}" begin="{f(max(t, .4 + i * .15))}s" dur=".8s" fill="freeze"/>{dot}'
                 f'<text x="{f(x)}" y="{y - 34}" text-anchor="middle" fill="{MARI2}" style="font:700 12px {SANS};letter-spacing:2.6px">{when}</text>'
                 f'<text x="{f(x)}" y="{y + 52}" text-anchor="middle" fill="{INK}" style="font:800 21px {SANS};letter-spacing:-.4px">{title}</text>'
                 f'<text x="{f(x)}" y="{y + 78}" text-anchor="middle" fill="{MUT}" style="font:500 14px {SANS}">{sub}</text>'
                 f'<rect x="{f(x - pw / 2)}" y="{y + 96}" width="{f(pw)}" height="22" rx="11" fill="{pill[1]}" stroke="{pill[0] if pill[1] == "none" else MARI}" stroke-opacity=".6"/>'
                 f'<text x="{f(x)}" y="{y + 111}" text-anchor="middle" fill="{pill[0]}" style="font:700 10px {SANS};letter-spacing:2.4px">{st}</text></g>')
    s.append("</svg>")
    return "".join(s)


if __name__ == "__main__":
    for name, fn in [("hero", hero), ("pipeline", pipeline), ("roadmap", roadmap)]:
        p = os.path.join(IMG, f"{name}.svg")
        open(p, "w", encoding="utf-8").write(fn())
        print(p, os.path.getsize(p) // 1024, "kB")
