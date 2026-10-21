"""Draws the front and back covers of the technical report (report/cover.pdf, report/backcover.pdf)."""
import math
import os
import random
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = A4
M = 2.3 * cm
LIB = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("Serif", f"{LIB}/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", f"{LIB}/LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Cond-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
AMBER, PAPER, GREY = colors.HexColor("#F2B544"), colors.HexColor("#ECE9E2"), colors.HexColor("#8B939E")


def night(c, seed=11, beam=True, logo=True):
    rnd = random.Random(seed)
    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        c.setFillColorRGB((5 + 12 * t) / 255, (7 + 17 * t) / 255, (10 + 22 * t) / 255)
        c.rect(0, H * (1 - (i + 1) / steps), W, H / steps + 1, stroke=0, fill=1)
    c.setFillColorRGB(.82, .85, .9)
    for _ in range(170):
        c.setFillAlpha(.15 + .5 * rnd.random()); x, y = rnd.random() * W, H * (.35 + .65 * rnd.random())
        c.circle(x, y, .3 + .6 * rnd.random(), stroke=0, fill=1)
    bx, by = W * .82, 0
    ang = math.radians(98); L = H * 1.05; sp = math.radians(4.5)
    if beam:
        for k, a in enumerate([.10, .07, .05]):
            c.setFillColorRGB(.95, .71, .27); c.setFillAlpha(a)
            p = c.beginPath(); w2 = sp * (1 + .5 * k)
            p.moveTo(bx - 4, by); p.lineTo(bx + math.cos(ang - w2) * L, by + math.sin(ang - w2) * L)
            p.lineTo(bx + math.cos(ang + w2) * L, by + math.sin(ang + w2) * L); p.close(); c.drawPath(p, stroke=0, fill=1)
    px, py = bx + math.cos(ang) * H * .66, by + math.sin(ang) * H * .66
    if logo:
        for rr, a in [(120, .05), (85, .08), (60, .12)]:
            c.setFillColorRGB(.95, .71, .27); c.setFillAlpha(a); c.circle(px, py, rr, stroke=0, fill=1)
        c.setFillAlpha(1); ls = 120
        c.drawImage(os.path.join(HERE, "logo.png"), px - ls / 2, py - ls / 2, width=ls, height=ls, mask="auto")
    x = -6
    while x < W + 10:
        w = 18 + rnd.random() * 46; h = H * (.07 + rnd.random() * .2) * (1.5 if rnd.random() < .12 else 1)
        c.setFillAlpha(1); c.setFillColorRGB(.012, .016, .024); c.rect(x, 0, w, h, stroke=0, fill=1)
        for yy in range(8, int(h) - 6, 9):
            for xx in range(5, int(w) - 5, 7):
                if rnd.random() < .11:
                    warm = rnd.random() > .72
                    c.setFillColor(colors.HexColor("#F2B544" if warm else "#5EC3FF")); c.setFillAlpha(.6 if warm else .25)
                    c.rect(x + xx, h - yy - 4, 2.2, 3.6, stroke=0, fill=1)
        x += w + rnd.random() * 3
    for i in range(80):
        c.setFillColorRGB(7 / 255, 9 / 255, 12 / 255); c.setFillAlpha(.92 * (1 - i / 80) ** 1.4)
        c.rect(0, i * 4, W, 4, stroke=0, fill=1)
    c.setFillAlpha(1)


def front(path):
    c = canvas.Canvas(path, pagesize=A4); c.setTitle("Beyond the 4 °C Alarm"); c.setAuthor("Suryansh Pratap Singh")
    night(c)
    c.setFillColor(AMBER); c.setFont("Mono", 8.5); c.drawString(M, H - M, "DAIRYGUARD  ·  OPEN RESEARCH")
    c.setFillColor(PAPER); c.setFont("Cond-Bold", 46); c.drawString(M, 250, "BEYOND THE")
    c.setFillColor(AMBER); c.drawString(M, 202, "4 °C ALARM")
    c.setFillColor(GREY); c.setFont("Serif", 13.5); c.drawString(M, 172, "What a temperature log can and cannot tell us about spoiling milk")
    c.setStrokeColor(AMBER); c.setLineWidth(1.2); c.line(M, 156, M + 46, 156)
    c.setFillColor(PAPER); c.setFont("Serif", 12.5); c.drawString(M, 74, "Suryansh Pratap Singh")
    c.setFillColor(GREY); c.setFont("Serif-Italic", 9.5)
    c.drawString(M, 59, "Shri Mata Vaishno Devi University")
    c.drawRightString(W - M, 59, "October 2026")
    c.showPage(); c.save()


def back(path):
    c = canvas.Canvas(path, pagesize=A4)
    night(c, seed=23, beam=False, logo=False)
    c.setFillColor(AMBER); c.setFont("Mono", 8.5); c.drawString(M, H - M, "BEYOND THE 4 °C ALARM")
    y = H - 6.2 * cm
    c.setFillColor(PAPER); c.setFont("Serif", 17)
    for line in ("A temperature log can say much about how much",
                 "growth the milk could have had, and little",
                 "about how much it did."):
        c.drawString(M, y, line); y -= 25
    y -= 18; c.setStrokeColor(AMBER); c.setLineWidth(1.2); c.line(M, y, M + 46, y); y -= 34
    c.setFillColor(GREY); c.setFont("Serif", 11.5)
    for line in ("240,000 simulated deliveries. One question: when a milk monitor is wrong,",
                 "what is it wrong about? The answer is not the thermometer. It is the",
                 "biology inside the carton, which no sensor can see, and which one",
                 "calorimetric test of the batch could largely recover,",
                 "as the simulation shows. Real milk is the next test.",
                 "",
                 "Open code, open data, every number reproducible from one command."):
        c.drawString(M, y, line); y -= 17
    c.setFillColor(AMBER); c.setFont("Mono", 9)
    c.drawString(M, 74, "github.com/CopyNinja07-07/dairyguard")
    c.setFillColor(GREY); c.drawRightString(W - M, 74, "copyninja07-07.github.io/dairyguard")
    c.showPage(); c.save()


if __name__ == "__main__":
    front(os.path.join(HERE, "cover.pdf")); back(os.path.join(HERE, "backcover.pdf")); print("covers ok")
