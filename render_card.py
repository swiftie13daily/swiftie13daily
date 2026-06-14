"""Render quiz cards: vibrant gradient backgrounds, grain, glow, white pills."""
import math
import os
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config  # noqa: F401  (kept for parity with the rest of the project)

# era -> (gradient_top, gradient_bottom, accent)
ERA_PALETTES = {
    "debut":      ("#3ee6a0", "#0b7a5c", "#fff3b0"),
    "fearless":   ("#ffd86b", "#e07b00", "#fffaf0"),
    "speak_now":  ("#d18bff", "#6a1fb5", "#ffe9ff"),
    "red":        ("#ff7a6b", "#a3121f", "#ffe8d6"),
    "1989":       ("#8fd8ff", "#1d4ed8", "#eaf6ff"),
    "reputation": ("#4b4b4b", "#0a0a0a", "#e9cf9a"),
    "lover":      ("#ffb3d9", "#8a5cf6", "#fff0f8"),
    "folklore":   ("#cfd8d4", "#5a7a6e", "#f5f7f2"),
    "evermore":   ("#ffb070", "#8a4513", "#fff3df"),
    "midnights":  ("#7b8cff", "#15183f", "#cdd5ff"),
    "ttpd":       ("#efe6d0", "#4a443c", "#ffffff"),
}
DEFAULT_PALETTE = ERA_PALETTES["midnights"]

# Font candidates: Linux (DejaVu) first, then Windows (Arial/Segoe UI), then macOS
FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "arialbd.ttf", "segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "arial.ttf", "segoeui.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
SIZE = 1080
INK = (30, 22, 50)  # dark text on white pills


def _font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _gradient(c1, c2):
    img = Image.new("RGB", (SIZE, SIZE))
    d = ImageDraw.Draw(img)
    a, b = _hx(c1), _hx(c2)
    for y in range(SIZE):
        t = y / SIZE
        d.line([(0, y), (SIZE, y)],
               fill=tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)))
    return img


def _glow(img, cx, cy, radius, color=(255, 255, 255), peak=110):
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(36, 0, -1):
        r = radius * i / 36
        alpha = int(peak * (1 - i / 36) ** 2)
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _grain(img, amount=7):
    arr = np.array(img.convert("RGB")).astype(np.int16)
    noise = np.random.randint(-amount, amount + 1, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))


def _sparkle(d, cx, cy, r, fill):
    pts = []
    for i in range(8):
        rad = r if i % 2 == 0 else r * 0.32
        a = math.pi / 2 + i * math.pi / 4
        pts.append((cx + rad * math.cos(a), cy - rad * math.sin(a)))
    d.polygon(pts, fill=fill)


def _shadow_text(d, xy, text, font, fill, anchor="mm"):
    x, y = xy
    d.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 110), anchor=anchor)
    d.text((x, y), text, font=font, fill=fill, anchor=anchor)


def _base(item):
    top, bottom, accent = ERA_PALETTES.get(item.get("era", ""), DEFAULT_PALETTE)
    img = _gradient(top, bottom)
    img = _glow(img, SIZE // 2, 360, 480)
    d = ImageDraw.Draw(img)
    acc = _hx(accent)
    _shadow_text(d, (SIZE // 2, 92), "SWIFTIE 13 DAILY", _font(FONT_BOLD, 46),
                 (255, 255, 255))
    _sparkle(d, 150, 92, 22, acc)
    _sparkle(d, SIZE - 150, 92, 22, acc)
    return img, d, acc


def render_card(item, out_path):
    img, d, acc = _base(item)
    diff = item.get("difficulty", "medium").upper()
    d.text((SIZE // 2, 158), f"DAILY QUIZ . {diff}", font=_font(FONT_REG, 36),
           fill=acc, anchor="mm")

    q_lines = textwrap.wrap(item["question"], width=28)
    y = 280
    fq = _font(FONT_BOLD, 58)
    for line in q_lines[:5]:
        _shadow_text(d, (SIZE // 2, y), line, fq, (255, 255, 255))
        y += 74

    y = max(y + 36, 568)
    letters = ["A", "B", "C", "D"]
    fo = _font(FONT_BOLD, 44)
    for i, opt in enumerate(item["options"][:4]):
        d.rounded_rectangle([(110, y), (SIZE - 110, y + 86)], radius=43,
                            fill=(255, 255, 255, 235))
        label = f"{letters[i]}   {opt}"
        if len(label) > 38:
            label = label[:35] + "..."
        d.text((165, y + 43), label, font=fo, fill=INK, anchor="lm")
        y += 110

    img = _grain(img)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


def render_answer(item, out_path):
    img, d, acc = _base(item)
    _shadow_text(d, (SIZE // 2, 250), "THE ANSWER IS...", _font(FONT_BOLD, 66),
                 (255, 255, 255))
    letters = ["A", "B", "C", "D"]
    i = item["answer_index"]
    d.rounded_rectangle([(100, 340), (SIZE - 100, 490)], radius=44,
                        fill=(255, 255, 255, 240))
    ans_lines = textwrap.wrap(f"{letters[i]}   {item['options'][i]}", width=26)
    fa = _font(FONT_BOLD, 56)
    y = 415 - (len(ans_lines) - 1) * 30
    for line in ans_lines[:3]:
        d.text((SIZE // 2, y), line, font=fa, fill=INK, anchor="mm")
        y += 62
    _sparkle(d, 140, 415, 26, acc)
    _sparkle(d, SIZE - 140, 415, 26, acc)

    d.text((SIZE // 2, SIZE - 64), "follow for a new quiz every day",
           font=_font(FONT_REG, 34), fill=acc, anchor="mm")
    img = _grain(img)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    sample = {
        "question": "What is Taylor Swift's famously lucky number?",
        "options": ["7", "13", "22", "3"],
        "answer_index": 1, "era": "debut", "difficulty": "easy",
        "fun_fact": "She was born on the 13th, and early in her career she wrote 13 on her hand before shows.",
    }
    print(render_card(sample, "output/posts/sample_test.png"))
