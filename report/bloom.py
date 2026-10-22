"""Paints the blurred lily used on the covers: aubergine at the heart, marigold light at the tips.

Each petal is a filled Bezier shape with a colour ramp along its length, blurred by its own amount,
so near petals are sharp and far ones soft, like a photograph with a shallow depth of field.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUB, ICE, MARI = (58, 15, 52), (221, 227, 232), (234, 170, 0)
INTER_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
INTER_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
INTER_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SERIF_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

LILY = [(0, (28, 5, 25, 255)), (.28, (58, 15, 52, 255)), (.5, (122, 42, 82, 245)), (.66, (234, 170, 0, 240)),
        (.86, (247, 213, 122, 230)), (1, (250, 240, 220, 200))]


def _bez(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + (t ** 3) * p3


def petal(img, cx, cy, ang, length, width, curl, blur, stops=LILY, alpha=1.0):
    """Draw one petal onto img (RGBA), rooted at (cx, cy) and pointing at angle ang (radians, 0 = up)."""
    L, Wd, C = length, width, curl
    a = _bez(np.array([0, 0]), np.array([Wd, -L * .22]), np.array([Wd * .95 + C * .4, -L * .72]), np.array([C, -L]))
    b = _bez(np.array([C, -L]), np.array([-Wd * .9 + C * .4, -L * .74]), np.array([-Wd * .7, -L * .24]), np.array([0, 0]))
    pts = np.vstack([a, b])
    ca, sa = math.cos(ang), math.sin(ang)
    rot = np.c_[pts[:, 0] * ca - pts[:, 1] * sa, pts[:, 0] * sa + pts[:, 1] * ca] + [cx, cy]
    pad = int(blur * 3 + 4)
    x0, y0 = np.floor(rot.min(0)).astype(int) - pad
    x1, y1 = np.ceil(rot.max(0)).astype(int) + pad
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(float(x - x0), float(y - y0)) for x, y in rot], fill=255)
    # colour ramp along the axis from base to tip
    tip = np.array([C * ca - (-L) * sa, C * sa + (-L) * ca])
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    t = np.clip(((xx - cx) * tip[0] + (yy - cy) * tip[1]) / (tip @ tip), 0, 1)
    offs = [s[0] for s in stops]
    rgba = np.stack([np.interp(t, offs, [s[1][k] for s in stops]) for k in range(4)], -1)
    rgba[..., 3] *= np.asarray(mask, float) / 255 * alpha
    layer = Image.fromarray(rgba.astype(np.uint8), "RGBA")
    # a bright vein along the middle
    vein = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vp = _bez(np.array([0, -L * .12]), np.array([C * .2, -L * .4]), np.array([C * .5, -L * .7]), np.array([C * .9, -L * .93]), 24)
    vr = [(float(x * ca - y * sa + cx - x0), float(x * sa + y * ca + cy - y0)) for x, y in vp]
    ImageDraw.Draw(vein).line(vr, fill=(255, 196, 70, int(170 * alpha)), width=max(2, int(Wd * .2)))
    vein = vein.filter(ImageFilter.GaussianBlur(blur + Wd * .08))
    layer = Image.alpha_composite(layer, vein)
    if blur > 0.3:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    _paste(img, layer, int(x0), int(y0))


def _paste(img, layer, x0, y0):
    """alpha_composite with the layer clipped to the image."""
    l, t = max(0, -x0), max(0, -y0)
    r, b = min(layer.width, img.width - x0), min(layer.height, img.height - y0)
    if r > l and b > t:
        img.alpha_composite(layer.crop((l, t, r, b)), (x0 + l, y0 + t))


def lily(img, cx, cy, S, depth=0.0, stem=True):
    """A lily of size S at (cx, cy). depth 0 is in focus; 1 is far and soft."""
    d = ImageDraw.Draw(img)
    if stem:
        st = Image.new("RGBA", img.size, (0, 0, 0, 0))
        p = _bez(np.array([cx, cy]), np.array([cx - S * .15, cy + S * .8]), np.array([cx - S * .7, cy + S * 1.2]), np.array([cx - S * 1.1, cy + S * 2.4]), 60)
        ImageDraw.Draw(st).line([tuple(map(float, q)) for q in p], fill=AUB + (200,), width=max(3, int(S * .035)))
        img.alpha_composite(st.filter(ImageFilter.GaussianBlur(2 + depth * 6)))
    angs = [-158, -116, -74, -34, 6, 46, 92, 132]
    blurs = [9, 2, .6, 5, 1, .8, 3, 12]
    k = S / 300
    for i, a in enumerate(angs):
        petal(img, cx, cy, math.radians(a), S * (.92 if i % 2 else 1.06), S * .2, S * (-.16 if i < 4 else .16),
              (blurs[i] + depth * 8) * k * 1.4, alpha=.94)
    sta = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sta)
    for j in range(6):
        a = math.radians(-120 + j * 14); r = S * (.5 + .1 * (j % 3))
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        ds.line([(cx, cy), (ex, ey)], fill=AUB + (190,), width=max(1, int(1.6 * k)))
        ds.ellipse([ex - 6 * k, ey - 3 * k, ex + 6 * k, ey + 3 * k], fill=MARI + (255,))
    img.alpha_composite(sta.filter(ImageFilter.GaussianBlur((1 + depth * 5) * k)))


def ground(w, h, dark=False, cols=8, margin=0):
    """Ice silver (or aubergine) ground with thin vertical grid lines and a soft marigold glow."""
    top, bot = ((233, 236, 238), (223, 228, 232)) if not dark else ((40, 9, 36), (58, 15, 52))
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g) * np.ones((1, w, 1))
    img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    line = (58, 15, 52, 13) if not dark else (234, 170, 0, 20)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(cols + 1):
        x = margin + (w - 2 * margin) * i / cols
        d.line([(x, 0), (x, h)], fill=line, width=max(1, w // 1600))
    return img


def glow(img, cx, cy, r, col=MARI, a=90):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * .45)))


def grain(img, amount=10, seed=3):
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.int16)
    n = rng.normal(0, amount, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def smear_text(img, xy, text, size, fill=AUB, smear=14, font=INTER_BLACK, tracking=-0.06, keep=True):
    """Heavy type with a horizontal motion blur trace behind a sharp copy."""
    f = ImageFont.truetype(font, size)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill + (255,))
        x += f.getlength(ch) + tracking * size
    if smear:
        w, h = lay.size
        sm = lay.resize((max(1, w // smear), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)
        sm = sm.filter(ImageFilter.GaussianBlur(2))
        img.alpha_composite(sm)
        img.alpha_composite(Image.fromarray((np.asarray(sm) * [1, 1, 1, .6]).astype(np.uint8), "RGBA"), (int(smear * 1.5), 0))
    if keep:
        img.alpha_composite(lay)
    return x


def text(img, xy, s, size, fill, font=INTER_SEMI, tracking=0.0, anchor="la"):
    f = ImageFont.truetype(font, size); d = ImageDraw.Draw(img)
    if not tracking:
        d.text(xy, s, font=f, fill=fill, anchor=anchor); return
    x, y = xy
    if anchor[0] == "r":
        x -= sum(f.getlength(c) + tracking * size for c in s)
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1]); x += f.getlength(ch) + tracking * size
