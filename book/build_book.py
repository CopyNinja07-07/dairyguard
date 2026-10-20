"""Builds the DairyGuard research book (PDF). Two passes: pass 1 learns page numbers, pass 2 prints them.
Numbers in the results chapter are read from results/base / results/lag / results/low CSVs, never typed by hand."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import csv
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image,
                                Table, TableStyle, KeepTogether, NextPageTemplate)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(HERE, "fig")
LIB = "/usr/share/fonts/truetype/liberation"
for nm, fn in (("Serif", "LiberationSerif-Regular"), ("Serif-Bold", "LiberationSerif-Bold"),
               ("Serif-Italic", "LiberationSerif-Italic"), ("Serif-BoldItalic", "LiberationSerif-BoldItalic")):
    pdfmetrics.registerFont(TTFont(nm, f"{LIB}/{fn}.ttf"))
pdfmetrics.registerFont(TTFont("Cond-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic", boldItalic="Serif-BoldItalic")

W, H = A4
M = 2.3 * cm
TITLE = "Beyond the 4 °C Alarm"
INK = colors.HexColor("#1b1b1a")
ACC = colors.HexColor("#1c5cab")
RULE = colors.HexColor("#c9c8c3")

body = ParagraphStyle("body", fontName="Serif", fontSize=10.6, leading=15.2, alignment=TA_JUSTIFY, textColor=INK, spaceAfter=7)
bodyl = ParagraphStyle("bodyl", parent=body, alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=9, leading=12, spaceAfter=3, alignment=TA_LEFT)
cap = ParagraphStyle("cap", parent=body, fontName="Serif-Italic", fontSize=9, leading=12, alignment=TA_LEFT, spaceBefore=3, spaceAfter=10)
h_ch = ParagraphStyle("h_ch", fontName="Serif-Bold", fontSize=21, leading=26, alignment=TA_CENTER, textColor=INK, spaceAfter=14, spaceBefore=4)
h_sec = ParagraphStyle("h_sec", fontName="Serif-Bold", fontSize=12.6, leading=16, textColor=INK, spaceBefore=10, spaceAfter=5, keepWithNext=1)
plan_t = ParagraphStyle("plan_t", parent=body, fontName="Serif-Bold", fontSize=11, leading=14, spaceAfter=2, alignment=TA_LEFT)
cell = ParagraphStyle("cell", fontName="Serif", fontSize=8.8, leading=11, textColor=INK, alignment=TA_LEFT)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Serif-Bold")
note = ParagraphStyle("note", parent=body, fontName="Serif-Italic", fontSize=9.6, leading=13.4, backColor=colors.HexColor("#f1f4f9"),
                      borderPadding=(6, 8, 6, 8), spaceBefore=6, spaceAfter=12, alignment=TA_LEFT)


class ChapterHeading(Paragraph):
    def __init__(self, key, text, style):
        super().__init__(text, style)
        self.key = key


def P(t, s=body):
    return Paragraph(t, s)


def table(rows, widths, head=True, zebra=True, fs=None):
    c_, cb_ = cell, cellb
    if fs:
        c_ = ParagraphStyle('cs', parent=cell, fontSize=fs, leading=fs + 2.2); cb_ = ParagraphStyle('cbs', parent=c_, fontName='Serif-Bold')
    data = [[Paragraph(str(c), cb_ if (head and i == 0) else c_) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
          ("LINEBELOW", (0, -1), (-1, -1), 0.5, RULE), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f6f6f4")))
    t.setStyle(TableStyle(st))
    return t


_fig_n = [0]


def figure(path, caption, width=None):
    _fig_n[0] += 1
    from PIL import Image as PI
    w, h = PI.open(path).size
    width = width or (W - 2 * M)
    img = Image(path, width=width, height=width * h / w)
    return KeepTogether([img, P(f"<b>Figure {_fig_n[0]}.</b> {caption}", cap)])


class Doc(BaseDocTemplate):
    def __init__(self, fn, total, pages_known):
        super().__init__(fn, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=2.4 * cm, bottomMargin=2.2 * cm,
                         title=f"{TITLE}: How Much Can Temperature History Tell Us About Spoiling Milk?",
                         author="Suryansh Pratap Singh", subject="Cold-chain monitoring research project")
        self.total = total
        self.page_of = {}
        fr = Frame(M, 2.2 * cm, W - 2 * M, H - 4.6 * cm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cov = Frame(M, 2 * cm, W - 2 * M, 4 * cm, id="c")
        self.addPageTemplates([PageTemplate(id="cover", frames=[cov], onPage=self._cover),
                               PageTemplate(id="body", frames=[fr], onPage=self._page)])

    def _cover(self, c, d):
        """Night-watch cover: a dark city, a signal light and the DairyGuard shield, drawn as vectors."""
        import random
        rnd = random.Random(11)
        c.saveState()
        steps = 60
        for i in range(steps):                                   # night sky gradient
            t = i / (steps - 1)
            r, g, b = (5 + 12 * t) / 255, (7 + 17 * t) / 255, (10 + 22 * t) / 255
            c.setFillColorRGB(r, g, b); c.rect(0, H * (1 - (i + 1) / steps), W, H / steps + 1, stroke=0, fill=1)
        c.setFillColorRGB(.82, .85, .9)
        for _ in range(170):                                     # stars
            c.setFillAlpha(.15 + .5 * rnd.random()); x, y = rnd.random() * W, H * (.35 + .65 * rnd.random())
            c.circle(x, y, .3 + .6 * rnd.random(), stroke=0, fill=1)
        bx, by = W * .82, 0                                      # signal light beam
        import math
        ang = math.radians(98); L = H * 1.05; sp = math.radians(4.5)
        for k, a in enumerate([.10, .07, .05]):
            c.setFillColorRGB(.95, .71, .27); c.setFillAlpha(a)
            pth = c.beginPath(); w2 = sp * (1 + .5 * k)
            pth.moveTo(bx - 4, by); pth.lineTo(bx + math.cos(ang - w2) * L, by + math.sin(ang - w2) * L)
            pth.lineTo(bx + math.cos(ang + w2) * L, by + math.sin(ang + w2) * L); pth.close(); c.drawPath(pth, stroke=0, fill=1)
        px, py = bx + math.cos(ang) * H * .66, by + math.sin(ang) * H * .66
        for rr, a in [(120, .05), (85, .08), (60, .12)]:          # halo
            c.setFillColorRGB(.95, .71, .27); c.setFillAlpha(a); c.circle(px, py, rr, stroke=0, fill=1)
        c.setFillAlpha(1)
        ls = 120                                                 # DairyGuard mark
        c.drawImage(os.path.join(HERE, "logo.png"), px - ls / 2, py - ls / 2, width=ls, height=ls, mask="auto")
        x = -6                                                   # skyline
        while x < W + 10:
            w = 18 + rnd.random() * 46; h = H * (.07 + rnd.random() * .2) * (1.5 if rnd.random() < .12 else 1)
            c.setFillColorRGB(.012, .016, .024); c.rect(x, 0, w, h, stroke=0, fill=1)
            for yy in range(8, int(h) - 6, 9):
                for xx in range(5, int(w) - 5, 7):
                    if rnd.random() < .11:
                        warm = rnd.random() > .72
                        c.setFillColor(colors.HexColor("#F2B544" if warm else "#5EC3FF")); c.setFillAlpha(.6 if warm else .25)
                        c.rect(x + xx, h - yy - 4, 2.2, 3.6, stroke=0, fill=1); c.setFillAlpha(1)
            x += w + rnd.random() * 3
        for i in range(80):                                      # fade behind the title
            c.setFillColorRGB(7 / 255, 9 / 255, 12 / 255); c.setFillAlpha(.92 * (1 - i / 80) ** 1.4)
            c.rect(0, i * 4, W, 4, stroke=0, fill=1)
        c.setFillAlpha(1)
        c.setFillColor(colors.HexColor("#F2B544")); c.setFont("Mono", 8.5)
        c.drawString(M, H - M, "THE STORYBOOK  ·  DAIRYGUARD RESEARCH")
        c.setFillColor(colors.HexColor("#ECE9E2")); c.setFont("Cond-Bold", 46)
        c.drawString(M, 250, "BEYOND THE")
        c.setFillColor(colors.HexColor("#F2B544")); c.drawString(M, 202, "4 °C ALARM")
        c.setFillColor(colors.HexColor("#8B939E")); c.setFont("Serif", 13.5)
        c.drawString(M, 172, "How much can a temperature log tell us about spoiling milk?")
        c.setStrokeColor(colors.HexColor("#F2B544")); c.setLineWidth(1.2); c.line(M, 156, M + 46, 156)
        c.setFillColor(colors.HexColor("#ECE9E2")); c.setFont("Serif", 12.5); c.drawString(M, 74, "Suryansh Pratap Singh")
        c.setFillColor(colors.HexColor("#8B939E")); c.setFont("Serif-Italic", 9.5)
        c.drawString(M, 59, "Mathematics and Computing, Shri Mata Vaishno Devi University")
        c.drawRightString(W - M, 59, "First edition · October 2026")
        c.restoreState()

    def _page(self, c, d):
        c.saveState()
        c.setFont("Serif", 9)
        c.setFillColor(colors.HexColor("#52514e"))
        c.drawRightString(W - M, H - 1.35 * cm, f"{d.page} of {self.total if self.total else '?'}")
        c.setFont("Serif-Italic", 8.5)
        c.drawString(M, 1.3 * cm, f"{TITLE} · Suryansh Pratap Singh")
        c.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, ChapterHeading):
            self.page_of[f.key] = self.page


# ------------------------------------------------------------------ content
def eq(tex, fs=14, name=None):
    """Render a LaTeX-style equation to a PNG with matplotlib mathtext and return a centred flowable."""
    import hashlib
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image as PI
    key = name or hashlib.md5(tex.encode()).hexdigest()[:10]
    path = os.path.join(FIG, f"eq_{key}.png")
    if not os.path.exists(path):
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0, 0, f"${tex}$", fontsize=fs, color="#1b1b1a", math_fontfamily="stix")
        fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)
    w, h = PI.open(path).size
    k = 72 / 300.0 * 0.95
    return Table([[Image(path, width=w * k, height=h * k)]], colWidths=[W - 2 * M], style=[("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)])


CH = [  # key, title, weight, plan description
    ("ch1", "The Warm Hour", 10,
     "The problem told through the milk itself: what a few warm hours do to a litre of it, why that matters for food waste and for health, and why a temperature log is not the same thing as an answer."),
    ("ch2", "What the Law Actually Says", 8,
     "A close reading of the FSSAI microbiological standards for milk: what the limits mean, what they were written for, and why that decides how a spoilage limit may honestly be defined."),
    ("ch3", "How Milk Spoils", 10,
     "A primer on predictive microbiology, from first principles: growth, lag, temperature, and shelf life as something that accumulates. What earlier work already built, and where the field is stuck."),
    ("ch4", "The Mathematics of a Warm Hour", 12,
     "The model written out and derived: the square-root law, the Baranyi-Roberts reference, the Gompertz shelf-life formula, the accumulator, and the statistics used to judge it. One worked example."),
    ("ch5", "Building the Machine", 15,
     "The computing side: the simulator, the benchmark, the tests, the parameter pipeline and the engineering decisions, including the mistakes that changed the result."),
    ("ch6", "Testing It Against Reality", 15,
     "Where every number comes from, a reproduction of a published experiment, and fits to real ComBase records for natural spoilage flora and for Listeria, with held-out checks."),
    ("ch7", "What a Thermometer Can and Cannot Tell Us", 20,
     "The results: a loss budget separating unobserved biology from sensing and sampling, comparisons against simple rules, and five parameter sets that all tell the same story."),
    ("ch8", "From Model to Machine", 5,
     "What the findings mean for the design of a real monitoring device, as design rules."),
    ("ch9", "Limits, and What Comes Next", 5,
     "What the study does not show, stated plainly, and the experiments that would turn it into a validated result."),
]
assert sum(c[2] for c in CH) == 100

REFS = [
    "FSSAI, <i>Appendix B: Microbiological Requirements</i>, Version 2 (04.11.2024), Tables 2A and 2B (milk and milk products). Food Safety and Standards Authority of India.",
    "K. Neumeyer, <i>Modelling pseudomonad growth in milk and milk-based products</i>, M.Sc. thesis, University of Tasmania (repository record eprints.utas.edu.au/21013).",
    "K. Neumeyer, T. Ross and T. A. McMeekin, “Development of a predictive model to describe the effects of temperature and water activity on the growth of spoilage pseudomonads,” <i>Int. J. Food Microbiol.</i>, vol. 38, pp. 45–54, 1997.",
    "K. Neumeyer, T. Ross, G. Thomson and T. A. McMeekin, “Validation of a model describing the effects of temperature and water activity on the growth of psychrotrophic pseudomonads,” <i>Int. J. Food Microbiol.</i>, vol. 38, pp. 55–63, 1997.",
    "H. Lin, M. Shavezipur, A. Yousef and F. Maleky, “Prediction of growth of <i>Pseudomonas fluorescens</i> in milk during storage under fluctuating temperature,” <i>J. Dairy Sci.</i>, vol. 99, pp. 1822–1830, 2016.",
    "F. Tarlak, “The use of predictive microbiology for the prediction of the shelf life of food products,” <i>Foods</i>, vol. 12, no. 24, art. 4461, 2023, doi:10.3390/foods12244461.",
    "E. Stavropoulou and E. Bezirtzoglou, “Predictive modeling of microbial behavior in food,” <i>Foods</i>, vol. 8, art. 654, 2019.",
    "V. Kumar, J. J. Ahire and N. K. Taneja, “Advancing microbial food safety and hazard analysis through predictive mathematical modeling,” <i>The Microbe</i>, vol. 2, art. 100049, 2024.",
    "O. R. Taiwo, H. Onyeaka, E. K. Oladipo, J. K. Oloke and D. C. Chukwugozie, “Advancements in predictive microbiology: integrating new technologies for efficient food safety models,” <i>Int. J. Microbiol.</i>, vol. 2024, art. 6612162, 2024, doi:10.1155/2024/6612162.",
    "I. J. Opara <i>et al.</i>, “AI-driven predictive microbiology with real-time sensors for next-generation food safety,” <i>J. Life Sci. Public Health</i>, vol. 1, no. 2, 2025, doi:10.69739/jlsph.v1i2.1299.",
    "L. Lima, A. I. Pereira, M. Pintado and M. Carocho, “Fresh dairy quality in the era of smart food systems: deterioration pathways, analytical technologies, and predictive modeling,” <i>Foods</i>, vol. 15, no. 19, art. 3439, 2026, doi:10.3390/foods15193439.",
    "C. N. Ugwu <i>et al.</i>, “Digital twins for food processing and shelf-life: linking mechanistic models, sensors, and AI to predict quality, safety, and waste through near-real-time decision support,” <i>Front. Food Sci. Technol.</i>, 2026, doi:10.3389/frfst.2026.1813819.",
    "N. H. Martin, P. Torres-Frenzel and M. Wiedmann, \u201cInvited review: Controlling dairy product spoilage to reduce food loss and waste,\u201d <i>J. Dairy Sci.</i>, vol. 104, pp. 1251\u20131261, 2021, doi:10.3168/jds.2020-19130.",
    "J. Baranyi and T. A. Roberts, \u201cA dynamic approach to predicting bacterial growth in food,\u201d <i>Int. J. Food Microbiol.</i>, vol. 23, pp. 277\u2013294, 1994.",
    "S. Tsaloumi, Z. Aspridou, E. Spyrelli, G.-J. E. Nychas and K. Koutsoumanis, \u201cDevelopment and validation of a mathematical model for pseudomonads growth as a basis for predicting spoilage of fresh poultry breast and thigh fillets,\u201d <i>Poultry Sci.</i>, vol. 101, art. 101985, 2022, doi:10.1016/j.psj.2022.101985.",
    "M. H. Zwietering, J. C. de Wit, H. G. A. M. Cuppers and K. van \u2019t Riet, \u201cModeling of bacterial growth with shifts in temperature,\u201d <i>Appl. Environ. Microbiol.</i>, pp. 204\u2013213, Jan. 1994.",
    "World Health Organization, \u201cWHO\u2019s first ever global estimates of foodborne diseases,\u201d news release, 3 Dec. 2015.",
    "ComBase (combase.cc), growth records in milk: aerobic spoilage bacteria in pasteurised milk (Tasmanian Institute of Agriculture; 51 records) and <i>Listeria monocytogenes</i> (99 records with a stated rate, 2-16 °C), accessed 19 Oct. 2026.",
    "A. Sofat and B. Sodhi, “Beyond thresholds: a quality-aware decision intelligence framework for cold chain IoT systems,” arXiv:2608.15082, 2026.",
    "S. Lau, A. Trmčić, N. H. Martin, M. Wiedmann and S. I. Murphy, “Development of a Monte Carlo simulation model to predict pasteurized fluid milk spoilage due to post-pasteurization contamination with gram-negative bacteria,” <i>J. Dairy Sci.</i>, vol. 105, pp. 1978–1998, 2022, doi:10.3168/jds.2021-21316.",
    "A. J. Buehler, N. H. Martin, K. J. Boor and M. Wiedmann, “Psychrotolerant spore-former growth characterization for the development of a dairy spoilage predictive model,” <i>J. Dairy Sci.</i>, vol. 101, pp. 6964–6981, 2018, doi:10.3168/jds.2018-14501.",
    "C. Qian, S. I. Murphy, T. T. Lott, N. H. Martin and M. Wiedmann, “Development and deployment of a supply-chain digital tool to predict fluid-milk spoilage due to psychrotolerant sporeformers,” <i>J. Dairy Sci.</i>, vol. 106, pp. 8414–8433, 2023, doi:10.3168/jds.2023-23673.",
    "M. C. Giannakourou and P. S. Taoukis, “Holistic approach to the uncertainty in shelf life prediction of frozen foods at dynamic cold chain conditions,” <i>Foods</i>, vol. 9, no. 6, art. 714, 2020, doi:10.3390/foods9060714.",
    "N. Ndraha, H.-I. Hsiao, J. Vlajic, M.-F. Yang and H.-T. V. Lin, “Time-temperature abuse in the food cold chain: review of issues, challenges, and recommendations,” <i>Food Control</i>, vol. 89, pp. 12–21, 2018.",
    "W. A. Müller, M. Kronbauer, S. B. Ferreira and S. B. da Silva, “Computational assessment of temperature failures in the cold supply chain: implications for beef shelf life,” <i>Food Control</i>, vol. 187, art. 112100, 2026, doi:10.1016/j.foodcont.2026.112100.",
    "V. M. Tashiguano <i>et al.</i>, “A multidisciplinary approach for predicting the microbiological spoilage of chicken breast fillets due to cold-chain disruption,” <i>J. Food Prot.</i>, vol. 89, art. 100754, 2026, doi:10.1016/j.jfp.2026.100754.",
    "M. C. Giannakourou and P. S. Taoukis, “Uncertainty and variability in post-processing kinetic calculations: nutritional quality loss in fruit juice products,” <i>J. Food Eng.</i>, vol. 390, art. 112403, 2025, doi:10.1016/j.jfoodeng.2024.112403.",
    "M. Göransson, F. Nilsson and Å. Jevinger, “Temperature performance and food shelf-life accuracy in cold food supply chains: insights from multiple field studies,” <i>Food Control</i>, vol. 86, pp. 332–341, 2018.",
    "J. Kim, C. A. Santos, B.-S. Kim, J. Kim and J. Koo, “Estimation of real-time remaining shelf life using mean kinetic temperature,” <i>LWT</i>, vol. 134, art. 109968, 2020.",
    "Y. Zou, J. Wu, X. Wang, K. Morales, G. Liu and A. Manzardo, “An improved artificial neural network using multi-source data to estimate food temperature during multi-temperature delivery,” <i>J. Food Eng.</i>, vol. 351, art. 111518, 2023, doi:10.1016/j.jfoodeng.2023.111518.",
]


def r(n):
    return f"[{n}]"


def front(page_of):
    s = []
    s.append(NextPageTemplate("body"))
    s.append(Spacer(1, 1))
    s.append(PageBreak())
    s.append(P(f"{TITLE}", h_ch))
    s.append(Spacer(1, 6))
    for t in [
        "There is a quiet moment in every cold chain when nobody is watching. A crate waits on a loading bay. A pouch sits in a shop in an open carton. A delivery bag rides for an hour on a hot afternoon. Nothing dramatic happens, and nothing is recorded. The milk simply gets warmer for a while, and then cold again.",
        "Most of us assume the damage depends on how warm it got. This book asks a more careful question: how much of the damage can a thermometer actually tell us? Bacteria in milk do not read thermometers. They grow at a rate that depends on temperature, but how many there were to begin with, which strains they were, and how the milk was handled before the logger started are all invisible to a temperature probe.",
        "So this is a book about limits as much as about a device. It builds a small, open, tested simulation of a milk cold chain, checks its biology against published experiments and against real records from a public database, and then asks how much a temperature record can and cannot predict. Some of the answer is encouraging. Some of it is humbling. Both parts are the point.",
        "It is written to be read as an engineer would read it: the models are derived, the code is open, every number can be traced to its source, and the places where the evidence is thin are marked where they occur.",
    ]:
        s.append(P(t))
    s.append(PageBreak())
    s.append(P("Synopsis", h_ch))
    for t in [
        "Milk travels through a long chain of hand-offs, and when the chain breaks nobody downstream has a record of what happened. A record of temperature can be turned into an estimate of how much of a milk's shelf life has been used, with growth models that have existed for decades. The open question is how far such an estimate can be trusted, and what limits it.",
        "The question here is narrow and testable. Given a temperature history, how well can an inexpensive on-device calculation tell whether milk will exceed a limit, and what limits that accuracy: the sensor, the sampling interval, the thermal mass of the product, the structure of the growth model, or biology that a thermometer cannot see? A detailed reference growth model plays the role of real milk, and the on-device calculation tries to predict it.",
        "The answer is a loss budget and a set of design rules. An oracle that knows each trip's true biology and temperature sets the ceiling, and information is removed step by step. In every parameter set tried, unobserved biology costs far more accuracy than the sensor or the sampling interval; a plain degree-hour count comes close to the full growth model; and a probability is better calibrated than a single alarm.",
        "The model is tied to data. It reproduces a published fluctuating-temperature experiment to within about 4%. Fitted to 51 real records of natural spoilage bacteria in pasteurised milk it shows that parameters from laboratory isolates overpredict growth by about 1.6 times. Fitted to real records for <i>Listeria monocytogenes</i>, a hazard organism, it predicts records it has not seen to within a factor of about 1.4, and the same design rules hold. Chapter 9 states what this does not show.",
    ]:
        s.append(P(t))
    s.append(PageBreak())
    s.append(P("What Is New Here", h_ch))
    s.append(P("Plenty of studies model how milk spoils, and plenty build better sensors. This one asks a different question, and the difference is the reason the book exists."))
    hd = ParagraphStyle("hd", parent=cellb, fontSize=10.5, leading=13, textColor=colors.white)
    cl = ParagraphStyle("cl", parent=cell, fontSize=9.6, leading=12.6)
    rows = [[P("The usual question", hd), P("The DairyGuard question", hd)],
            [P("Which input moves the outcome most?", cl), P("Given a temperature log, what is a monitor still blind to?", cl)],
            [P("Temperature is an unknown drawn at random, so it naturally ranks first.", cl), P("Temperature is measured, as a real monitor would measure it.", cl)],
            [P("Measures how much shelf life varies.", cl), P("Measures how well a device can predict spoilage, against a known true answer.", cl)],
            [P("Sensors and logging intervals are assumed, not tested.", cl), P("Accuracy is removed one source at a time: unseen biology, sensor error, sampling interval, choice of rule.", cl)],
            [P("Comparisons across separate runs.", cl), P("Every comparison is made on the same trips, with a paired bootstrap.", cl)]]
    tb = Table(rows, colWidths=[(W - 2 * M) / 2] * 2)
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#3a4757")), ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#b07a12")),
                            ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#fdf6e7")), ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    s += [tb, Spacer(1, 14)]
    s.append(P("What was found", h_sec))
    s.append(P("Three suspects were tested. A better thermometer gains at most about 2 points of accuracy (AUC, on a 50 to 100 scale). Reading every minute instead of every hour makes no measurable difference in most settings. A smarter growth-based rule beats a plain degree-hour count by at most about 4 points. The one thing no thermometer can see, which bacteria were in the milk and how many, costs 9 to 40 points. The pattern held in all five simulated worlds, including one for the pathogen <i>Listeria</i>."))
    s.append(P("The plot twist", h_sec))
    s.append(P("Earlier studies find that temperature matters most, and this book finds that biology matters most. Both are right. When nobody logs the trip, how warm it got is the biggest unknown. Once a monitor records it, what is left unexplained is mostly the milk itself. That second situation is the one a cold-chain monitor is in, and it is the one this book measures."))
    s.append(PageBreak())
    s.append(P("Chapter Plan", h_ch))
    for i, (k, t, w, d) in enumerate(CH, 1):
        pg = page_of.get(k, "?")
        s.append(P(f"Chapter {i}: {t} (Page {pg})", plan_t))
        s.append(P(d, bodyl))
        
        s.append(Spacer(1, 3))
    return s


def ch1():
    s = [ChapterHeading("ch1", "Chapter 1: The Warm Hour", h_ch)]
    s += [P("Take a litre of pasteurised milk that has just left the dairy. It is not sterile. Pasteurisation kills nearly everything that grows in the cold, but a few cells get back in afterwards, from a filler, a pipe, a gasket, a crate. A review of dairy spoilage puts post-pasteurisation contamination, often with <i>Pseudomonas</i>, behind about half to three-fifths of the microbial spoilage of fluid milk, and places the onset of quality deterioration near one million cells per millilitre, seven to ten days after pasteurisation [13]. Real loads straight after pasteurisation are tiny, of the order of one to fifty cells in 100 millilitres [13]."),
          P("Those few cells are on a clock, and the clock is set by temperature. A laboratory study of <i>Pseudomonas fluorescens</i> in milk held it at 4 °C and subjected it to two warm periods of four hours at 29 °C. Milk kept cold the whole time reached a million cells per millilitre in about 90 hours. The milk with two warm mornings reached it in about 55 [5]. Eight hours of warmth, spread over two days, took roughly 40% off its life."),
          P("This is the warm hour of the title. It is not dramatic. It happens on a loading bay, in a van, in a shop's open carton, and it is invisible to everyone downstream of it. The milk looks the same. It is only the clock inside it that has moved."),
          P("Chapter 4 gives the arithmetic of that clock. Here, one number is enough: with the parameters used in this book, a two-hour excursion to 18 °C in an insulated crate uses up about 7% of a shelf life, which is about six hours of refrigerated life, and a simple alarm that checks whether a threshold was crossed cannot say so."),
          P("<b>Why it matters to people.</b> Spoiled milk is first of all wasted food and wasted money. But temperature control is also a health matter. The World Health Organization estimated in 2015 that foodborne disease causes about 600 million illnesses and 420,000 deaths a year worldwide, and in its South-East Asia region, which includes India, more than 150 million cases and 175,000 deaths a year [17]. Those deaths come mainly from agents such as norovirus, non-typhoidal <i>Salmonella</i> and pathogenic <i>E. coli</i>, and the estimates are not specific to milk. This book does not claim that temperature logging prevents any particular number of deaths. It claims something smaller and checkable: that the growth of bacteria in milk responds strongly to temperature, that this includes <i>Listeria monocytogenes</i>, a pathogen that grows at refrigerator temperatures (Chapter 6 measures how fast, from real records), and that therefore a record of temperature has value if it can be turned into a sound judgement."),
          P("<b>The trouble with a record.</b> A temperature log says how warm the milk was. It does not say how many bacteria there were at the start, which strains they were, or how long they had already been adapting. Two crates with the same log can be at very different places. So the question this book asks is not whether to log temperature. It is how much a log can say once everything else is accounted for."),
          P("<b>What is in this book.</b> Chapter 2 reads the Indian standards for milk carefully, because a device that reports a verdict must read them correctly. Chapter 3 explains how milk spoils. Chapter 4 writes the model down and derives it. Chapter 5 describes the software, how it was built and how it was tested. Chapter 6 checks the model against published experiments and against real data. Chapter 7 gives the results. Chapter 8 turns them into design rules for a device, and Chapter 9 says what is still unknown."),
          P("If a reader keeps only three things, they are these. First, <b>biology is the limit</b>: what a thermometer cannot see costs far more accuracy than any choice of sensor. Second, <b>simple rules come close</b>: a degree-hour count recovers almost everything a full growth model does. Third, <b>say the uncertainty</b>: a probability is better calibrated than a yes-or-no alarm.", note)]
    return s


def ch2():
    s = [PageBreak(), ChapterHeading("ch2", "Chapter 2: What the Law Actually Says", h_ch)]
    s += [P("The FSSAI microbiological standards for milk and milk products are set out in Appendix B of the regulations [1]. They are easy to misread, and a device that claims to report a safe-or-not verdict must read them correctly."),
          P("<b>The limit that is often quoted.</b> For pasteurised or boiled milk and flavoured milk, Table 2A gives a three-class plan for aerobic plate count: n = 5 samples, c = 3, m = 3 x 10<super>4</super> per mL and M = 5 x 10<super>4</super> per mL. Coliforms use n = 5, c = 0 and a limit of less than 10 per mL. The test methods named are IS 5402 / ISO 4833 for plate count (pour plate at 30 °C) and IS 5401 Part 1 / ISO 4832 for coliforms."),
          P("<b>What the plan means.</b> In a three-class plan a lot is satisfactory if every value is at or below m. It is acceptable if no more than c values lie between m and M and the rest are at or below m. It is unsatisfactory if any value exceeds M or more than c values exceed m. So 3 x 10<super>4</super> and 5 x 10<super>4</super> are not interchangeable: one is m, the other is M."),
          P("<b>What Table 2A is for.</b> The standard says the process hygiene criteria in Table 2A indicate the acceptable functioning of the production process. They are not to be used as requirements for releasing products to the market, and they apply at the end of the manufacturing process. They are values above which corrective action is required to keep the process hygienic."),
          P("<b>What Table 2B is for.</b> The food safety criteria define the acceptability of a batch and apply at the end of manufacture and during shelf life. For pasteurised milk the criteria listed are <i>Salmonella</i> and <i>Listeria monocytogenes</i>, each absent in 25 mL (n = 5, c = 0). Table 2B lists no <i>Bacillus cereus</i> criterion for pasteurised milk."),
          P("<b>Sampling and handling.</b> For regulatory sampling the standard requires samples to be stored and transported below 5 °C, not frozen, so that analysis can start within 24 hours. Regulatory testing uses five samples at each of three accredited laboratories, with no retesting."),
          P("<b>Consequences for this book.</b> First, the plate-count limit in Table 2A is a process hygiene marker, not an end-of-shelf-life rule. The study therefore evaluates two spoilage limits and names them honestly: scenario A uses 3 x 10<super>4</super> CFU/mL as a quality marker, and scenario B uses 10<super>6</super> CFU/mL, the level near which a dairy-spoilage review places the onset of quality deterioration [13]. Second, for the hazard organism in Chapter 6 the standard says absent in 25 mL, and a temperature record cannot establish absence. The case study therefore asks only how much <i>growth</i> a record implies, with labels of half a log and one log of growth. These are round-number labels and not regulatory limits. Third, any consumer report should say <i>estimated risk</i> and never <i>safe</i>.")]
    return s


def ch3():
    s = [PageBreak(), ChapterHeading("ch3", "Chapter 3: How Milk Spoils", h_ch)]
    s += [P("Predictive microbiology describes how populations of microorganisms change with conditions, using primary models for growth over time, secondary models for how the growth parameters depend on temperature or other factors, and tertiary tools that package these for users [6, 7, 9]. Reviews of the field describe two-step fitting, in which primary and secondary models are fitted in sequence, and one-step fitting, in which they are fitted together [6]."),
          P("<b>Three phases.</b> A small population in fresh milk does nothing visible at first, a stretch called the lag phase, during which cells adjust. It then grows exponentially, doubling at a steady rate, and finally levels off when it runs out of room or food. Plotted on a logarithmic scale this is an S-shaped curve. For spoilage the interesting part is how long it takes to climb from a handful of cells per millilitre to a million."),
          P("<b>The square-root law.</b> A common secondary model for psychrotrophic bacteria in cold storage is the square-root relation of Ratkowsky: the square root of the maximum specific growth rate is proportional to the distance above a notional minimum growth temperature. A University of Tasmania thesis fitted this to 68 growth curves of a fast-growing <i>Pseudomonas putida</i> in broth and in milk and found a minimum temperature of -7.7 °C [2]. The same thesis compiled 64 literature values and found the average to be 265.4 K (about -7.75 °C), the same for isolates from dairy and from meat. The consequence is easy to state: growth does not stop at 0 °C. It slows, and each extra degree above the minimum speeds it more than the last."),
          P("<b>Shelf life as something that accumulates.</b> If the time to reach the limit at a constant temperature is SL, then a period of time at that temperature uses up the fraction (time / SL) of the shelf life. Adding these fractions over a whole trip gives the cumulative shelf life used. When it reaches 1, the limit has been reached. The calculation is cheap enough for a microcontroller: one table lookup and one addition per reading."),
          figure(os.path.join(FIG, "trace.png"), "One trip in the model. Top: ambient and milk temperature. Middle: reference growth (Baranyi) against the 3 x 10<super>4</super> CFU/mL marker. Bottom: cumulative shelf life used, with and without the excursion. Starting load is an assumed value.", W - 2 * M - 1.8 * cm),
          P("<b>What was already built.</b> The idea of turning a temperature log into a spoilage estimate for milk is not new, and this book does not claim it. The Tasmanian thesis [2] developed a milk <i>Pseudomonas</i> temperature model, validated it in the laboratory and with industry participants, put it into prototype software, and reviewed time-temperature integrators and loggers. A 2022 poultry study used the same square-root form with fitted limits [15]. A 2016 milk study modelled growth under fluctuating temperature [5], and a 1994 study examined growth after temperature shifts [16]. A 2026 preprint builds a decision framework on temperature streams from cold-chain sensors, combining a simple growth model, a recurrent neural network and a language model, and evaluates it in simulation for pasteurised milk [19]. The closest studies in spirit are uncertainty and sensitivity analyses of shelf-life simulations. A Cornell Monte Carlo model of fluid-milk spoilage found that growth rate and storage temperature move the share of spoiled containers most, ahead of the starting count, with lag the least influential [20]; the same group models spore-former spoilage at a constant 6 °C, where the maximum growth rate again mattered most [21], and in a later version with temperatures that change along the supply chain found home storage temperature, transport temperature and the starting spore count most influential, released as a digital tool [22]. Two 2026 studies measure what temperature abuse costs: short failures cut simulated beef shelf life by up to 10% and intermittent ones by up to 60% [25], and cyclic abuse of chicken breast shifted the flora towards <i>Pseudomonas</i> and sped up spoilage [26]. Another group separated kinetic uncertainty from cold-chain temperature variability for a frozen food [23] and later added raw-material variability for vitamin C in juice, where temperature again mattered most [27]. In all of these the temperature is an unknown input drawn from a distribution, so it naturally ranks high. On the monitoring side, Swedish field data showed large gaps between dynamically predicted and printed shelf life, with retail display the weakest stage [28]; mean kinetic temperature has been used to estimate remaining shelf life of chicken and milk [29]; and a neural network that estimates product temperature from vehicle and door data shows that temperature errors of 1 and 2 °C translate into about 10% and 20% shelf-life error under a simple model [30]. A review catalogues how often cold chains break [24]. None of these asks how much a temperature monitor loses to unseen biology, to its sensor, to how often it samples and to its rule, against a known answer. The two views fit together: when the temperature is unknown it dominates; once it is logged, what is left is mostly biology. That comparison is what this book is about."),
          P("<b>What the recent reviews say is missing.</b> A 2026 review of fresh dairy quality and predictive modelling reports that few studies predict the end of shelf life, that endpoint definition is a major methodological gap, that few models are validated beyond their development data, and that realistic time-temperature testing is uncommon; it recommends prediction intervals or failure probabilities in place of single deterministic estimates [11]. A 2026 review of digital twins for shelf life of fresh-cut produce discusses uncertainty-aware predictions and calibration but, by its own account, reports no original experiments [12]. Earlier reviews survey models and sensors without testing how much each source of error matters [6-10]. None of this work measures how large each source of error is on a common footing. That is the gap this book addresses.")]
    return s


def ch4():
    s = [PageBreak(), ChapterHeading("ch4", "Chapter 4: The Mathematics of a Warm Hour", h_ch)]
    s += [P("This chapter writes the model down. Nothing in it is new mathematics: the pieces come from the predictive-microbiology literature cited in Chapter 3. What is new is putting them in one place, checking each step, and being explicit about which part plays the role of reality and which part plays the role of the device."),
          P("4.1  Temperature to growth rate", h_sec),
          P("Let N be the number of cells per millilitre and y = ln N. In the exponential phase, growth is dy/dt = &mu;, where &mu; is the specific growth rate in 1/h. The square-root law says &mu; depends on temperature T as"),
          eq(r"\sqrt{\mu(T)} = b\,(T - T_{\min}), \quad T > T_{\min}", name="sqrt"),
          P("with two constants per organism: a slope b and a notional minimum growth temperature T<sub>min</sub>. Both are found by linear regression: plot the square root of measured growth rates against temperature and fit a straight line, so that the slope is b and T<sub>min</sub> = &minus;(intercept)/b. With the Neumeyer parameters b = 0.030 and T<sub>min</sub> = &minus;7.7 °C [2], growth at the refrigerator temperature of 4 °C is"),
          eq(r"\mu(4\,^{\circ}\mathrm{C}) = \left(0.030 \times 11.7\right)^2 \approx 0.123\ \mathrm{h}^{-1}", name="mu4"),
          P("which is a doubling time of ln 2 / 0.123 = 5.6 hours. At 13 °C the same law gives (0.030 x 20.7)<super>2</super> = 0.386 per hour, 3.1 times faster. Because the temperature enters squared, a rise from 4 to 13 °C, which is a rise of 9 degrees in a gap of 11.7, more than triples the growth rate."),
          P("4.2  The reference model: growth with a memory", h_sec),
          P("Real populations do not start growing at full speed. The Baranyi-Roberts model [14] captures this with a hidden state q that measures how ready the cells are, and growth is throttled by the factor q / (1 + q):"),
          eq(r"\dfrac{dy}{dt} = \mu(T)\,\dfrac{q}{1+q}\,\left(1 - e^{\,y - y_{\max}}\right)", name="bar1"),
          eq(r"\dfrac{dq}{dt} = \mu(T)\,q, \quad h_0 = \ln\left(1 + \dfrac{1}{q_0}\right), \quad \lambda\mu = h_0", name="bar2"),
          P("The state q grows at the same pace as the population, so the lag shortens when the temperature is high and lengthens when it is low, and the product of lag and growth rate stays constant for cells with the same history. That constant, h<sub>0</sub>, is the only lag parameter. The last factor in the first equation is a ceiling, y<sub>max</sub>, the largest count the milk can support. Because &mu; is evaluated at the current temperature, the model handles any temperature trace with no further work: it is integrated forward one minute at a time in this book. This is the stand-in for real milk."),
          P("4.3  The device model: a closed-form shelf life", h_sec),
          P("The device cannot integrate differential equations on every reading, so it uses a different primary model that has a closed form: the modified Gompertz curve,"),
          eq(r"\log_{10} N(t) = \log_{10} N_0 + A\,\exp\left[-\exp\left(\dfrac{\mu_{10}\,e}{A}(\lambda - t) + 1\right)\right]", name="gomp"),
          P("where A is the total rise in log<sub>10</sub> from start to ceiling, &mu;<sub>10</sub> = &mu; / ln 10 is the growth rate per log<sub>10</sub> and &lambda; = h<sub>0</sub> / &mu; is the lag. Setting the left side to the log<sub>10</sub> of a limit N<sub>L</sub> and solving for t gives the time for the population to reach the limit at constant temperature T:"),
          eq(r"\mathrm{SL}(T) = \dfrac{h_0}{\mu(T)} + \dfrac{A}{\mu_{10}(T)\,e}\left[1 - \ln\left(-\ln\dfrac{L}{A}\right)\right]", name="sl"),
          P("with L = log<sub>10</sub> N<sub>L</sub> &minus; log<sub>10</sub> N<sub>0</sub>. This is the shelf life at temperature T. The two models are structurally different on purpose. If the device used the same equations as the reference it would only be copying the truth, and the benchmark would be circular."),
          P("4.4  Accumulating shelf life", h_sec),
          P("A reading T<sub>i</sub> held for a time &Delta;t<sub>i</sub> uses up the fraction &Delta;t<sub>i</sub> / SL(T<sub>i</sub>) of the shelf life. Summing over a trip gives the cumulative shelf life used, and the device says the limit has been reached when it reaches 1:"),
          eq(r"\mathrm{CSL} = \sum_i \dfrac{\Delta t_i}{\mathrm{SL}(T_i)}", name="csl"),
          P("This is one lookup in a precomputed table and one addition per reading. Why should it be hard to beat with something simpler? Because SL(T) is roughly a constant divided by the growth rate, so"),
          eq(r"\mathrm{SL}(T) \approx \dfrac{C}{\mu(T)} \ \Rightarrow\ \mathrm{CSL} \approx \dfrac{1}{C}\int \mu\left(T(t)\right) dt", name="approx"),
          P("The accumulator is, to a good approximation, the time integral of the growth rate. A degree-hour count above 4 °C is the time integral of (T &minus; 4)<sub>+</sub>, a first-order stand-in for the same thing, since the growth rate is nearly linear in temperature over a few degrees. Two quantities that are both integrals of increasing functions of temperature will rank most trips the same way. That is the mathematical reason Chapter 7 finds simple rules competitive, and it is also why the comparison is honest about what it can and cannot show."),
          P("4.5  A worked example", h_sec),
          P("A crate at 4 °C is exposed to 18 °C air for two hours. The milk has thermal mass, so it warms toward 18 °C with a time constant of two hours and reaches about 13 °C before the air cools again. The growth rate at 13 °C is 3.1 times the rate at 4 °C, so for the part of the excursion spent near 13 °C each hour costs about three hours of refrigerated life, and the warm-up and cool-down add the rest. Integrating the accumulator over the trace gives a cumulative shelf life of 1.52 in place of 1.45 for a trip that stayed at 4 °C: about 7% of one shelf life, which with a label life of 83 hours is about six hours."),
          P("4.6  How skill is measured", h_sec),
          P("Each simulated trip is spoiled or not, according to the reference model. Each score the device computes (the accumulator, or a simple rule) is a number per trip, and the question is how well it separates the two groups. The area under the ROC curve answers this without choosing a threshold:"),
          eq(r"\mathrm{AUC} = P\left(s_{\mathrm{spoiled}} > s_{\mathrm{ok}}\right) + \dfrac{1}{2}\,P\left(s_{\mathrm{spoiled}} = s_{\mathrm{ok}}\right)", name="auc"),
          P("It is the probability that a randomly chosen spoiled trip scores higher than a randomly chosen good one. A value of 0.5 means no skill and 1.0 means perfect separation. Confidence intervals come from resampling trips with replacement (the bootstrap). To compare two scores on the same trips the same resampled trips are used for both, which is the paired bootstrap and is the valid way to test a difference in AUC on shared data."),
          P("When the device reports a probability p<sub>k</sub> for trip k and the true outcome is o<sub>k</sub> (0 or 1), two numbers measure its quality. The Brier score is the mean squared error of the probabilities. The expected calibration error groups trips into bins B<sub>m</sub> by predicted probability and averages the gap between the predicted and the observed frequency:"),
          eq(r"\mathrm{Brier} = \dfrac{1}{n}\sum_{k=1}^{n}(p_k - o_k)^2, \quad \mathrm{ECE} = \sum_{m} \dfrac{|B_m|}{n}\left|\bar{o}_m - \bar{p}_m\right|", name="cal"),
          P("A probability that says 70% should be right about 70% of the time. ECE measures how far this is from being true.")]
    return s


def ch5():
    s = [CondPageBreak(10 * cm), ChapterHeading("ch5", "Chapter 5: Building the Machine", h_ch)]
    s += [P("This chapter is about the software: what was written, how the pieces fit, how they were checked, and which mistakes changed the results. The model is mechanistic, not trained on data in the machine-learning sense. Its parameters are fitted by simple regression to published growth rates, and it is then tested against separate published results and against its own mathematical properties."),
          P("5.1  The pieces", h_sec)]
    rows = [["Module", "What it does"],
            ["kinetics", "Square-root growth rate, closed-form Gompertz shelf life, an interpolated lookup for fast use, and a numerical Baranyi-Roberts integrator. About 100 lines."],
            ["simulate", "The trip generator (temperature traces with random excursions and thermal inertia), the reference growth along each trace, sensor models and the five scores. Vectorised with NumPy so thousands of trips run at once."],
            ["benchmark", "Runs all settings, computes AUC with bootstrap intervals, the paired contrasts, and the Monte Carlo probability with Brier score and calibration error. Fixed random seeds."],
            ["validate", "Fits the model to published rates and to ComBase records, and reproduces the published fluctuating-temperature experiment."],
            ["summarize", "Condenses every run into the numbers quoted in the paper, the book and the web page, so that no figure is typed by hand."],
            ["web", "A JavaScript port of the kernel for the companion web page, checked against the Python values (an automated test confirms agreement to nine decimal places)."]]
    s.append(table(rows, [2.6 * cm, 12.8 * cm]))
    s.append(Spacer(1, 8))
    s += [P("5.2  The benchmark, step by step", h_sec),
          P("<b>1. Draw a trip.</b> Base temperature is drawn from 2.5 to 5 °C. Excursions occur at an average of one per 144 hours of horizon, peaking at 12, 14.3, 17.5 or 30.7 °C with weights 0.30, 0.25, 0.30 and 0.15, and last a median of 60 minutes (lognormal, clipped to 10 to 480 minutes). Product temperature follows ambient with a first-order time constant: 5 to 20 minutes for a low-mass pouch, 1 to 4 hours for an insulated crate."),
          P("<b>2. Grow the truth.</b> Draw the trip's biology: minimum temperature around its mean, a lognormal multiplier on the slope with coefficient of variation 0, 0.10 or 0.25, the lag state from a measured range, and a starting load. Integrate the Baranyi-Roberts model along the trace. A trip is spoiled if the population exceeds the limit within the label horizon."),
          P("<b>3. Measure.</b> Add a sensor model to the true temperature: a fixed offset drawn per trip, random noise and quantisation. DS18B20 offsets are within 0.5 °C, PT1000 within 0.15 °C. Sample at 1, 15 or 60 minutes, or adaptively."),
          P("<b>4. Score.</b> Compute the accumulator and four simple rules (degree-hours above 4 °C, time above 5 °C, time above 8 °C, maximum temperature). Compute the oracle too, which uses the trip's true parameters and noise-free temperature."),
          P("<b>5. Compare.</b> Compute AUC with bootstrap intervals, paired differences between methods on the same trips, and the loss budget from oracle to real score. For the probability score, draw 80 parameter sets from a prior, run the accumulator under each, and report the fraction that reach the limit."),
          P("<b>The label horizon.</b> The horizon is defined the way a printed shelf life is defined in practice: the time the estimator takes to reach the limit at constant 4 °C, rounded up to whole hours. This gives 83 hours for scenario A and 113 hours for scenario B in the baseline. The choice was made from label balance alone, before any method comparison was examined. It makes about half of all trips spoiled by construction, so the results must not be read as real-world spoilage rates."),
          P("<b>Model-structure risk.</b> The baseline truth and the device share the assumption that growth follows temperature instantly. Published work shows that real cells can add lag after a temperature shift [5, 16]. A second run therefore re-imposes a quarter of the lag state whenever product temperature departs from, or returns to, its two-hour running mean by more than 4 °C, which is the fraction Zwietering and colleagues found. The device is not told about this."),
          P("5.3  How it was tested", h_sec),
          P("Fourteen automated tests run in a few seconds. They check: the Gompertz shelf life against the exponential-growth estimate; agreement of the two growth models in isothermal conditions with matched parameters; the lookup against the closed form; monotonic decrease of shelf life with temperature; the AUC function against a reference implementation and known cases; the paired bootstrap on identical scores (difference exactly zero) and on a real improvement; the probability score against cold and warm histories; the calibration metric on perfect and worst-case inputs; the reproduction of the published milk experiment within 10%; and the agreement of the JavaScript demo with the Python kernel."),
          P("5.4  Mistakes that changed the result", h_sec),
          P("Four problems were found, and each changed the numbers. They are listed because a reader should know that the model was corrected by checking it against sources, not accepted on first run."),
          P("<b>A horizon that hid the problem.</b> The first run used a fixed 144-hour horizon and found almost no spoiled trips, so every method looked perfect. The horizon was redefined to the printed-shelf-life rule above."),
          P("<b>A growth slope that was 3.5 times too low.</b> A placeholder slope of 0.016 never reached a million cells in 140 hours. When two published sources were read, it was replaced by 0.030 and 0.027, which agree. The benchmark was re-run."),
          P("<b>A confidence interval read as a spread.</b> The 0.7 K interval on the minimum growth temperature in the thesis is the 95% interval of a mean over 64 sources, not the spread between strains, which is 2.8 K. The simulation now uses an assumed 1.5 K, between the two, and says so."),
          P("<b>A level that was wrong for real flora.</b> Parameters from inoculated isolates overpredict growth of natural spoilage flora by about 1.6 times when compared with real ComBase records (Chapter 6). The benchmark was re-run with fitted parameters, and the conclusions held."),
          P("5.5  Reproducibility", h_sec),
          P("Every number in the paper and in this book is read from result files by a script. The repository holds the code, the 14 tests, the parameter file with provenance for each value (Appendix A), and one command that regenerates the tables and figures (Appendix B).")]
    return s


def ch6():
    import validate_lin as V
    import json
    cb = json.load(open(os.path.join(ROOT, "results", "validation_combase.json")))
    ls = json.load(open(os.path.join(ROOT, "results", "validation_lis.json")))
    r = V.res
    s = [CondPageBreak(9 * cm), ChapterHeading("ch6", "Chapter 6: Testing It Against Reality", h_ch)]
    s += [P("A simulation is only as believable as its inputs. This chapter records where each biological number comes from, and then asks three questions of real data: does the model reproduce a published experiment, do its parameters describe natural spoilage bacteria, and does the same law describe a hazard organism."),
          P("6.1  Two independent sources agree", h_sec),
          P("Neumeyer's thesis [2] gives a square-root slope of 0.00465 for the square root of the reciprocal generation time in minutes, with T<sub>min</sub> = &minus;7.7 °C, from 68 growth curves. Converted to hours and natural-log growth, this is b = 0.030. Lin and colleagues [5] report growth rates of 0.056, 0.17 and 0.46 per hour at 4, 15 and 29 °C for <i>P. fluorescens</i> in milk. Fitting the square-root law to those three values gives b = %.3f and T<sub>min</sub> = %.1f °C." % (r["b_ln"], r["T0_C"])),
          P("At 4 °C the Neumeyer parameters imply a generation time of 5.6 hours; Lin and colleagues measured 6.4 hours. Different organisms, different media and different laboratories, and the two agree to within about 15%%. The lag state, the product of lag and growth rate, is %.1f from Lin's lag of 29.5 hours at 4 °C, and ranges from 3.0 to 5.0 across their three temperatures. The simulation draws it from 2.5 to 5.0." % r["h0_at_4C"]),
          P("6.2  A published fluctuating-temperature experiment", h_sec),
          P("Lin and colleagues also held milk at 4 °C and subjected it to two warm periods of four hours at 29 °C, the first after 24 hours and the second 24 hours after the first ended. They report that milk at constant 4 °C reached 10<super>6</super> CFU/mL in about 90 hours and that the two warm periods cut this to about 55 hours. With parameters fitted only to their growth rates and their lag at 4 °C, the kernel used in this book gives %.0f hours at constant 4 °C and %.0f hours with the two excursions." % (r["h0_at_4C_const_h"], r["h0_at_4C_two_excursions_h"])),
          figure(os.path.join(FIG, "lin.png"), "Reproduction of a published experiment. Lines: this study's Baranyi kernel, with parameters fitted from the published growth rates. Diamonds: the times to 10<super>6</super> CFU/mL reported by Lin et al. [5] (about 90 h and about 55 h).", W - 2 * M - 1.2 * cm)]
    rows = [["Quantity", "Published", "This study", "Difference"],
            ["Time to 10<super>6</super> at constant 4 °C (h)", "about 90", "%.0f" % r["h0_at_4C_const_h"], "%+.0f%%" % (100 * (r["h0_at_4C_const_h"] - 90) / 90)],
            ["Time to 10<super>6</super> after two 4 h excursions to 29 °C (h)", "about 55", "%.0f" % r["h0_at_4C_two_excursions_h"], "%+.0f%%" % (100 * (r["h0_at_4C_two_excursions_h"] - 55) / 55)]]
    s.append(table(rows, [7.0 * cm, 2.8 * cm, 3.2 * cm, 2.4 * cm]))
    s.append(Spacer(1, 6))
    s += [P("The growth rates and the 4 °C lag were used to fit the parameters, so the constant 4 °C result is close by construction. The result after two excursions was not used in fitting. It is the real test, and it is a small one: the published times are approximate values read from the text, not curves, and it is one experiment with one organism in inoculated UHT milk at a starting load of about 800 CFU/mL, far above the load expected after pasteurisation [13]."),
          P("6.3  Natural spoilage bacteria: ComBase", h_sec),
          P("The studies above inoculated milk with a chosen <i>Pseudomonas</i>. What spoils real pasteurised milk is a natural mixture. ComBase, a public database of microbial growth records, holds %d records of the maximum growth rate of aerobic spoilage bacteria in pasteurised milk at 2.7 to 14.9 °C, from the Tasmanian Institute of Agriculture. The square-root law fits them well (R<super>2</super> about 0.9 on the square-root scale), with b = %.4f and T<sub>min</sub> = %.1f °C [18]." % (cb["robust"]["n"] + 1, cb["robust"]["b_ln"], cb["robust"]["Tmin_C"])),
          P("The parameters from the inoculated studies <i>overpredict</i> these records. The bias factor is %.2f and the accuracy factor %.2f, which means predicted growth is about 1.6 times too fast at every temperature. The shape is right and the level is not. Natural spoilage flora in pasteurised milk grows more slowly than an isolate chosen for being fast, which agrees with the thesis choosing its fastest strain as a worst case [2]. The scatter around the fitted curve has a standard deviation of about 16%% in the growth rate, a useful empirical anchor for the strain-variability axis used in Chapter 7, though it also contains experimental noise." % (cb["neumeyer"]["bias_factor"], cb["neumeyer"]["accuracy_factor"])),
          figure(os.path.join(FIG, "combase.png"), "Maximum growth rate of aerobic spoilage bacteria in pasteurised milk (ComBase records, grey) against the three parameter sets. The Neumeyer- and Lin-anchored curves are about 1.6 times too fast; the fitted curve is in blue.", W - 2 * M - 1.2 * cm),
          P("6.4  A hazard organism: <i>Listeria monocytogenes</i>", h_sec),
          P("<i>Listeria monocytogenes</i> is a pathogen that, unlike most, grows at refrigerator temperatures. The same ComBase search for milk returned records for it. Those with a stated rate at 2 to 16 °C were split by condition. The %d records with no added factors were used to fit the square-root law, and the %d records with other stated conditions (sterilised or previously heated milk, added salts or acids) were held out and predicted without refitting." % (ls["n_fit"], ls["n_heldout"])),
          P("The fit gives b = %.4f (95%% bootstrap interval %.4f to %.4f) and T<sub>min</sub> = %.1f °C (%.1f to %.1f °C). A generation time at 4 °C of %.0f hours means growth is slow in a good refrigerator, but it speeds up steeply: at 13 °C it is %.1f times faster, against about 3.1 times for the spoilage flora (Figure 4). On the held-out records the bias factor is %.2f and the accuracy factor %.2f, so predictions are on average within a factor of about 1.4. The split is by condition and not by study, so some held-out records share a source with fitted ones, and this is a weaker test than a split by study would be." % (ls["b_ln"], ls["b_ci95"][0], ls["b_ci95"][1], ls["Tmin_C"], ls["Tmin_ci95"][0], ls["Tmin_ci95"][1], ls["generation_time_4C_h"], ls["rate_ratio_13C_vs_4C"], ls["heldout_bias_accuracy"][0], ls["heldout_bias_accuracy"][1])),
          figure(os.path.join(FIG, "lis.png"), "<i>Listeria monocytogenes</i> in milk. Left: ComBase records, the fit and the held-out records. Right: growth rate relative to 4 °C for the two organism classes. A warm hour costs a pathogen more because its minimum growth temperature is closer to refrigeration.", W - 2 * M - 0.6 * cm),
          P("6.5  Where the data came from, and how complete it is", h_sec),
          P("The ComBase records were taken from the database's search results for milk. For each record we kept the organism, the temperature, the stated maximum growth rate and the other stated conditions (pH, water activity, added salts or acids, heat treatment)."),
          P("Of about 480 milk records, 373 were taken, of which 179 state a growth rate; 131 require curve fitting and were not used. Nearly all records are for pathogens, so the spoilage-flora set is 51 records for aerobic spoilage bacteria in pasteurised milk. The fits are consistent with the literature: the <i>Listeria</i> minimum temperature of about &minus;2 °C is in the range usually reported for this organism.")]
    return s


def ch8():
    s = [CondPageBreak(9 * cm), ChapterHeading("ch8", "Chapter 8: From Model to Machine", h_ch)]
    s += [P("The findings in Chapter 7 are about any temperature record, whether it comes from a commercial data logger or a stick-on probe. Temperature loggers and time-temperature indicators are already products; this book does not survey them. What the study adds is a ranking of what matters when one is designed, and the ranking is not the one a hardware project would guess."),
          P("<b>Rule 1: spend little on the thermometer.</b> A digital DS18B20 probe, specified at plus or minus 0.5 °C, is within about 0.01 to 0.02 AUC of a PT1000 read through a MAX31865 converter, which is specified at about plus or minus 0.15 °C. A better probe is a poor way to improve a spoilage estimate."),
          P("<b>Rule 2: sample every 15 to 60 minutes.</b> Under the assumed excursion model, hourly sampling is indistinguishable from every-minute sampling in most settings. An adaptive rule that samples faster when the product is warm or changing gave no detectable advantage either. The caveat is the excursion model: if short, sharp excursions are common, this would change."),
          P("<b>Rule 3: compute degree-hours first, add the growth model if cheap.</b> A degree-hour count above 4 °C recovers nearly all the skill of the accumulator. The accumulator costs one lookup per reading, so it is nearly free on a microcontroller, and it adds a small, consistent edge, larger when extra lag after temperature shifts is present."),
          P("<b>Rule 4: spend effort on the biology.</b> The largest loss is what a thermometer cannot see: starting load, strain, lag. A design that records handling history, supports a cheap load or hygiene proxy, or lets a supervisor enter a batch's age could recover part of this. No sensor upgrade can."),
          P("<b>Rule 5: report a probability, and never the word 'safe'.</b> A single yes-or-no alarm was poorly calibrated in every run. A probability from a set of plausible parameters was much better. For the hazard organism the standard asks for absence, which a temperature record cannot establish, so a report should say <i>estimated risk</i>.")]
    return s


def ch9():
    s = [CondPageBreak(10 * cm), ChapterHeading("ch9", "Chapter 9: Limits, and What Comes Next", h_ch)]
    items = [
        ("Partly assumed biology.", "The growth slope, minimum temperature and lag state are sourced or fitted. The strain spread, the starting load, the carrying capacity, the excursion pattern and the <i>Listeria</i> lag are assumed (Appendix A). The spread in minimum temperature is the most uncertain: the thesis reports a 95% interval of 0.7 K on the mean, but the spread between sources is 2.8 K, and the value used here (1.5 K for spoilage flora) lies between them."),
        ("Shared structure.", "The reference and the device both turn the temperature history into something close to the time integral of the growth rate (Chapter 4). So the benchmark does not test whether a kinetic score beats a simple rule because it models growth better. It tests how much accuracy is lost to the sources of error listed. The structure-risk run relaxes one part of this by adding extra lag after shifts, but other structural failures, such as adaptation, population effects and species interactions, are not tested."),
        ("Constructed prevalence.", "About half of the spoilage trips and 8 to 38% of the <i>Listeria</i> trips are positive by construction. AUC does not depend on prevalence, but predictive values and calibration do, so calibration results show relative differences between methods and not absolute performance in the field."),
        ("Two organism classes.", "The main model stands in for psychrotrophic spoilage bacteria, and a case study covers <i>Listeria monocytogenes</i>. A review of dairy spoilage reports that about 40 to 50% of fluid-milk spoilage in the United States comes instead from spore-forming gram-positive bacteria, which grow later and differently [13]. Nothing here estimates illness risk, which depends on dose, virulence, the host and the contamination event."),
        ("Rates, not curves.", "Records are maximum rates from many sources and methods, not curves, so lag and responses to temperature shifts are not tested on them. The <i>Listeria</i> held-out test is by condition, not by study."),
        ("Assumed trip generator.", "Excursion frequency, duration and the independence of trips are assumptions. Real chains have correlated failures, such as one bad truck affecting many pouches."),
        ("One published validation experiment.", "The model reproduces one published experiment, with approximate values read from the text. No new plate counts have been measured."),
        ("Position in the literature.", "Temperature-driven shelf-life estimates are not new (Chapter 3). The contribution here is the decomposition of prediction error, and its standing rests on the related work reviewed in Chapter 3.")]
    s.append(P("These limits are listed so a reader, a reviewer or a co-author can find them without searching."))
    for t, d in items:
        s.append(P(f"<b>{t}</b> {d}"))
    s += [P("What comes next", h_sec),
          P("Four pieces of work would turn this into a validated result, in order of effort. First, extend the ComBase data to more spoilage organisms and to full growth curves, not only rates. Second, calibrate the sensors against a reference thermometer and measure the thermal time constants of real packs; this needs only a stirred bath, a reference thermometer and a refrigerator. Third, measure real plate counts of spoilage flora in commercial pasteurised milk under constant and fluctuating temperature, and predict the fluctuating groups blind, in a food microbiology laboratory with a supervisor and only organisms already present in commercial milk. Fourth, run a field logging study. The code, tests and data are open so that anyone can repeat or extend it.")]
    return s


def appendix_a():
    s = [PageBreak(), ChapterHeading("appA", "Appendix A: Parameter Provenance", h_ch)]
    s.append(P("Every number the simulation uses that did not come from a measurement or a source is marked <b>assumed</b>. The values are read directly from the project's parameter file."))
    with open(os.path.join(ROOT, "data", "params.csv"), newline="", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    t = [["Parameter", "Value", "Provenance"]]
    for x in rows:
        prov = x["provenance"].replace("<", "&lt;").replace(">", "&gt;")
        t.append([x["parameter"].replace("_", " "), x["value"].replace("<", "&lt;"), prov])
    s.append(table(t, [3.2 * cm, 3.3 * cm, 8.9 * cm], fs=8.0))
    return s


def appendix_b():
    s = [PageBreak(), ChapterHeading("appB", "Appendix B: Reproducing the Results", h_ch)]
    s += [P("The repository contains everything needed to regenerate the numbers, tables and figures in the paper and in this book from fixed random seeds."),
          P("<b>Layout.</b> <font face='Courier'>src/</font> holds the kernel, the simulator, the benchmark and the validation scripts; <font face='Courier'>tests/</font> holds the 14 tests; <font face='Courier'>data/</font> holds the parameter table; <font face='Courier'>results/</font> holds the output of each benchmark run; <font face='Courier'>paper/</font>, <font face='Courier'>book/</font> and <font face='Courier'>demo/</font> hold the sources of the manuscript, this book and the interactive demo; <font face='Courier'>docs/</font> is the published website with the finished PDFs."),
          P("<b>Commands.</b> <font face='Courier'>make test</font> runs the tests. <font face='Courier'>make runs</font> repeats the five benchmark runs (about three hours on two cores). <font face='Courier'>make summary</font> condenses them, <font face='Courier'>make paper</font> and <font face='Courier'>make book</font> rebuild the documents, and <font face='Courier'>make all</font> does everything. Individual runs are selected by environment variables, for example <font face='Courier'>DG_PARAMS=lis python3 src/benchmark_v2.py 4000 results/lis</font>."),
          P("<b>Runs reported.</b> (a) Baseline with sourced biology; (b) the same with extra lag after temperature shifts; (c) a sensitivity run with a realistic low starting load; (d) a run with the growth parameters fitted to the ComBase records of natural spoilage flora; (e) a run for <i>Listeria monocytogenes</i> with parameters fitted to ComBase records. An earlier run with placeholder parameters showed the same overall pattern and is not reported."),
          P("<b>Licence and archive.</b> The code is released under the MIT licence, with a citation file; a persistent archive identifier can be added when a version is deposited.")]
    return s


def references():
    s = [PageBreak(), ChapterHeading("refs", "References", h_ch)]
    for i, t in enumerate(REFS, 1):
        s.append(P(f"[{i}] {t}", ParagraphStyle("ref", parent=body, fontSize=9.0, leading=11.6, leftIndent=22, firstLineIndent=-22, alignment=TA_LEFT, spaceAfter=3.5)))
    return s


def results_chapter():
    from results_chapter import build as rc
    return rc(ROOT, FIG, ChapterHeading, P, h_sec, figure, table, note, body, W, M)


def story(page_of):
    s = []
    s += front(page_of)
    s += [PageBreak()]
    s += ch1()
    s += ch2()
    s += ch3()
    s += ch4()
    s += ch5()
    s += ch6()
    s += [PageBreak()] + results_chapter()
    s += ch8()
    s += ch9()
    s += appendix_a()
    s += appendix_b()
    s += references()
    return s


def build(out):
    _fig_n[0] = 0
    d1 = Doc(out + ".pass1.pdf", 0, {})
    d1.build(story({}))
    pages = dict(d1.page_of)
    total = d1.page
    _fig_n[0] = 0
    d2 = Doc(out, total, pages)
    d2.build(story(pages))
    d3 = Doc(out, d2.page, pages)
    _fig_n[0] = 0
    d3.build(story(d2.page_of))
    os.remove(out + ".pass1.pdf")
    return d3.page


if __name__ == "__main__":
    n = build(os.path.join(ROOT, "docs", "DairyGuard_Storybook.pdf"))
    print("pages", n)
