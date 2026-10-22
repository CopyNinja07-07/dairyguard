"""Draws the front and back covers of the book (report/cover.pdf, report/backcover.pdf).

The art is painted with bloom.py at 200 dpi and placed full-bleed on an A4 page.
"""
import io
import os

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

import bloom as B

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1654, 2339          # A4 at 200 dpi
M = 150                    # margin in pixels
INK, MUT = B.AUB + (255,), (102, 82, 95, 255)


def place(img, path, title):
    c = canvas.Canvas(path, pagesize=A4); c.setTitle(title); c.setAuthor("Suryansh Pratap Singh")
    buf = io.BytesIO(); img.convert("RGB").save(buf, "JPEG", quality=80, dpi=(200, 200)); buf.seek(0)
    c.drawImage(ImageReader(buf), 0, 0, width=A4[0], height=A4[1])
    c.showPage(); c.save()


def front(path):
    img = B.ground(W, H, margin=M)
    B.glow(img, W * .66, H * .36, W * .34, a=70)
    B.lily(img, W * .28, H * .86, W * .16, depth=1)
    B.lily(img, W * .66, H * .36, W * .30)
    img = B.grain(img, 4)
    B.text(img, (M, M), "DAIRYGUARD  ·  OPEN RESEARCH", 26, INK, B.INTER_SEMI, .32)
    B.text(img, (W - M, M), "OCTOBER 2026", 26, INK, B.INTER_SEMI, .32, "ra")
    B.text(img, (M, M + 70), "A CLEANER", 22, INK, B.INTER_SEMI, .34)
    B.text(img, (M, M + 104), "COLD CHAIN", 22, INK, B.INTER_SEMI, .34)
    sz, y0 = 250, H * .43
    B.smear_text(img, (M - 12, y0), "Beyond", sz, smear=10)
    B.smear_text(img, (M + 150, y0 + sz * .86), "the 4 °C", sz, smear=18)
    B.smear_text(img, (M + 420, y0 + sz * 1.72), "Alarm.", sz, smear=8)
    B.text(img, (M, y0 + sz * 2.95), "What a temperature log can and cannot", 50, INK, B.SERIF_IT)
    B.text(img, (M, y0 + sz * 2.95 + 64), "tell us about spoiling milk", 50, INK, B.SERIF_IT)
    B.text(img, (M, H - M - 70), "SURYANSH PRATAP SINGH", 30, INK, B.INTER_SEMI, .3)
    B.text(img, (M, H - M - 22), "Shri Mata Vaishno Devi University", 30, MUT, B.INTER_MED)
    B.text(img, (W - M, H * .45), "01", 24, INK, B.INTER_SEMI, .2, "ra")
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for i in range(6):
        d.line([(W - M - (30 if i == 0 else 14), H * .45 + 40 + i * 12), (W - M, H * .45 + 40 + i * 12)], fill=INK if i == 0 else (58, 15, 52, 110), width=3)
    place(img, path, "Beyond the 4 °C Alarm")


def back(path):
    img = B.ground(W, H, dark=True, margin=M)
    B.glow(img, W * .5, H * .98, W * .5, a=110)
    B.lily(img, W * .80, H * .90, W * .22, depth=.7, stem=False)
    img = B.grain(img, 4)
    ICE, MARI, SOFT = B.ICE + (255,), B.MARI + (255,), (201, 185, 198, 255)
    B.text(img, (M, M), "BEYOND THE 4 °C ALARM", 26, MARI, B.INTER_SEMI, .32)
    y = 520
    for line in ("A temperature log can say much", "about how much growth the milk", "could have had, and little about", "how much it did."):
        B.text(img, (M, y), line, 74, ICE, B.SERIF_IT); y += 92
    y += 60
    for line in ("240,000 simulated deliveries. One question: when a milk monitor is wrong,",
                 "what is it wrong about? The answer is not the thermometer. It is the",
                 "biology inside the carton, which no sensor can see, and which one",
                 "calorimetric test of the batch could largely recover, as the simulation",
                 "shows. Real milk is the next test.",
                 "",
                 "Open code, open data, every number reproducible from one command."):
        B.text(img, (M, y), line, 36, SOFT, B.INTER_MED); y += 56
    B.text(img, (M, H - M - 20), "github.com/CopyNinja07-07/dairyguard", 28, MARI, B.INTER_SEMI)
    B.text(img, (W - M, H - M - 20), "copyninja07-07.github.io/dairyguard", 28, SOFT, B.INTER_SEMI, 0, "ra")
    place(img, path, "Beyond the 4 °C Alarm")


if __name__ == "__main__":
    front(os.path.join(HERE, "cover.pdf")); back(os.path.join(HERE, "backcover.pdf")); print("covers ok")
