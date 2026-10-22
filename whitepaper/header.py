"""Paints the title band at the top of each white paper (whitepaper/head-wp01.jpg, head-wp02.jpg)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "report"))
import bloom as B  # noqa: E402

W, H, M = 1654, 760, 150    # A4 width at 200 dpi
INK = B.AUB + (255,)


def band(path, code, title, second, kicker):
    img = B.ground(W, H, margin=M)
    B.glow(img, W * .78, H * .5, W * .22, a=70)
    B.lily(img, W * .78, H * .56, W * .19, stem=True)
    img = B.grain(img, 4)
    B.text(img, (M, 96), f"DAIRYGUARD WHITE PAPER {code}", 24, INK, B.INTER_SEMI, .32)
    B.text(img, (W - M, 96), "OCTOBER 2026", 24, INK, B.INTER_SEMI, .32, "ra")
    B.text(img, (M, 150), kicker, 20, (102, 82, 95, 255), B.INTER_SEMI, .34)
    B.smear_text(img, (M - 8, 250), title, 190, smear=10)
    B.smear_text(img, (M + 120, 250 + 168), second, 190, smear=16)
    img.convert("RGB").save(path, "JPEG", quality=82, dpi=(200, 200))


if __name__ == "__main__":
    band(os.path.join(HERE, "head-wp01.jpg"), "WP-01", "DairyGuard", "Kinetic.", "THE ARCHITECTURE")
    band(os.path.join(HERE, "head-wp02.jpg"), "WP-02", "DairyGuard", "Batch.", "THE BLUEPRINT")
    print("bands ok")
