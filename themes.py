"""
themes.py — Visual Themes & Procedural Islamic Art for NoorPost Ultimate
Implements 7 curated visual themes with high-resolution vector geometry,
gradients, atmospheric effects, and graceful local fallbacks.
Zero external heavy asset dependencies required.
"""

import math
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw

# ─────────────────────────────────────────────
# 7 CURATED ISLAMIC THEMES
# ─────────────────────────────────────────────
THEMES = {
    # 1. Midnight Black and Gold
    "midnight-gold": {
        "name": "Midnight Black and Gold",
        "description": "Elegant obsidian black backgrounds with tasteful royal gold typography and geometric stars.",
        "bg_top": (10, 12, 16),
        "bg_bottom": (4, 5, 8),
        "gold": (212, 175, 55),          # Pure Islamic Gold
        "gold_dim": (135, 105, 36),       # Warm Dim Gold
        "text_primary": (245, 243, 237),  # Soft White
        "text_secondary": (145, 155, 170),# Subtle Slate
        "accent": (212, 175, 55),
        "glow": (200, 160, 50),
        "is_light": False,
        "style": "midnight_gold",
    },

    # 2. Emerald Serenity
    "emerald-serenity": {
        "name": "Emerald Serenity",
        "description": "Deep forest and emerald greens with soft gradients and refined Islamic arch decoration.",
        "bg_top": (6, 26, 18),
        "bg_bottom": (3, 14, 10),
        "gold": (210, 178, 75),
        "gold_dim": (115, 95, 38),
        "text_primary": (238, 248, 240),
        "text_secondary": (118, 156, 132),
        "accent": (70, 150, 105),
        "glow": (30, 100, 65),
        "is_light": False,
        "style": "emerald_serenity",
    },

    # 3. Minimal White
    "minimal-white": {
        "name": "Minimal White",
        "description": "Clean, tranquil white and parchment backgrounds with crisp typography and subtle gold accents.",
        "bg_top": (252, 250, 246),
        "bg_bottom": (244, 240, 232),
        "gold": (168, 128, 42),          # Antique Gold
        "gold_dim": (195, 160, 85),
        "text_primary": (28, 34, 42),     # Deep Charcoal
        "text_secondary": (105, 115, 128),# Slate Gray
        "accent": (168, 128, 42),
        "glow": (220, 205, 170),
        "is_light": True,
        "style": "minimal_white",
    },

    # 4. Peaceful Nature
    "peaceful-nature": {
        "name": "Peaceful Nature",
        "description": "Earth tones, dawn horizon gradients, and gentle mountain silhouette accents.",
        "bg_top": (14, 28, 36),
        "bg_bottom": (8, 18, 24),
        "gold": (225, 190, 80),
        "gold_dim": (130, 105, 40),
        "text_primary": (242, 246, 244),
        "text_secondary": (130, 165, 150),
        "accent": (85, 140, 120),
        "glow": (40, 90, 80),
        "is_light": False,
        "style": "peaceful_nature",
    },

    # 5. Reflective Night
    "reflective-night": {
        "name": "Reflective Night",
        "description": "Deep celestial indigo with soft moonlight, radiant crescent, and atmospheric stars.",
        "bg_top": (8, 14, 32),
        "bg_bottom": (4, 7, 18),
        "gold": (220, 185, 70),
        "gold_dim": (110, 125, 165),
        "text_primary": (240, 245, 255),
        "text_secondary": (140, 160, 200),
        "accent": (160, 195, 255),
        "glow": (60, 95, 180),
        "is_light": False,
        "style": "reflective_night",
    },

    # 6. Masjid Elegance
    "masjid-elegance": {
        "name": "Masjid Elegance",
        "description": "Royal midnight twilight featuring majestic mosque domes and minaret silhouettes.",
        "bg_top": (12, 16, 28),
        "bg_bottom": (6, 8, 16),
        "gold": (218, 175, 52),
        "gold_dim": (135, 105, 35),
        "text_primary": (245, 242, 235),
        "text_secondary": (135, 145, 165),
        "accent": (180, 140, 45),
        "glow": (140, 105, 30),
        "is_light": False,
        "style": "masjid_elegance",
    },

    # 7. Ramadan and Eid
    "ramadan-eid": {
        "name": "Ramadan and Eid",
        "description": "Celebratory midnight sapphire and violet with glowing lanterns (fanous) and festive crescents.",
        "bg_top": (22, 12, 38),
        "bg_bottom": (10, 5, 20),
        "gold": (235, 190, 55),
        "gold_dim": (155, 115, 35),
        "text_primary": (254, 252, 246),
        "text_secondary": (175, 150, 195),
        "accent": (235, 190, 55),
        "glow": (160, 90, 180),
        "is_light": False,
        "style": "ramadan_eid",
    },
}

# Aliases for convenience
THEME_ALIASES = {
    "dark-gold": "midnight-gold",
    "midnight": "midnight-gold",
    "emerald": "emerald-serenity",
    "green": "emerald-serenity",
    "white": "minimal-white",
    "minimal": "minimal-white",
    "nature": "peaceful-nature",
    "night": "reflective-night",
    "masjid": "masjid-elegance",
    "mosque": "masjid-elegance",
    "ramadan": "ramadan-eid",
    "eid": "ramadan-eid",
}

def resolve_theme(theme_name: Optional[str] = None) -> Dict[str, Any]:
    """Resolve theme configuration with aliases and default fallback."""
    if not theme_name:
        theme_name = "midnight-gold"
    normalized = theme_name.strip().lower().replace("_", "-")
    canonical = THEME_ALIASES.get(normalized, normalized)
    return THEMES.get(canonical, THEMES["midnight-gold"])

# ─────────────────────────────────────────────
# PROCEDURAL GEOMETRIC & ARTWORK DRAWING HELPERS
# ─────────────────────────────────────────────

def draw_8point_star(draw: ImageDraw.ImageDraw, cx: float, cy: float,
                     r_out: float, r_in: float, fill_color: tuple, outline_color: Optional[tuple] = None):
    """Draw a classic Islamic 8-pointed geometric star (Khatim Sulayman)."""
    points = []
    for i in range(16):
        angle = i * (math.pi / 8.0) - (math.pi / 2.0)
        r = r_out if i % 2 == 0 else r_in
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill_color, outline=outline_color)

def draw_crescent_moon(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                       radius: int, fill_color: tuple, bg_color: tuple, offset_x: int = 14):
    """Draw a radiant Islamic crescent moon (Hilal)."""
    # Outer circle
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill_color)
    # Inner cutout circle shifted to form crescent
    inner_r = int(radius * 0.92)
    cut_x = cx + offset_x
    cut_y = cy - int(radius * 0.12)
    draw.ellipse([cut_x - inner_r, cut_y - inner_r, cut_x + inner_r, cut_y + inner_r], fill=bg_color)

def draw_hanging_lantern(draw: ImageDraw.ImageDraw, cx: int, top_y: int, height: int,
                         body_color: tuple, glow_color: tuple):
    """Draw an authentic Islamic hanging lantern (Fanous) with glowing candle."""
    # Hanging chain
    chain_bottom = top_y + int(height * 0.28)
    draw.line([(cx, top_y), (cx, chain_bottom)], fill=body_color, width=2)

    # Top dome cap
    cap_w = int(height * 0.18)
    cap_h = int(height * 0.08)
    draw.polygon([
        (cx - cap_w, chain_bottom + cap_h),
        (cx, chain_bottom),
        (cx + cap_w, chain_bottom + cap_h),
    ], fill=body_color)

    # Lantern glass chamber
    body_top = chain_bottom + cap_h
    body_h = int(height * 0.40)
    body_bottom = body_top + body_h
    body_w_mid = int(height * 0.24)
    body_w_base = int(height * 0.16)

    # Glass polygon
    draw.polygon([
        (cx - cap_w, body_top),
        (cx + cap_w, body_top),
        (cx + body_w_mid, body_top + body_h // 2),
        (cx + body_w_base, body_bottom),
        (cx - body_w_base, body_bottom),
        (cx - body_w_mid, body_top + body_h // 2),
    ], outline=body_color, width=2)

    # Inner warm glowing candle core
    candle_cx = cx
    candle_cy = body_top + body_h // 2
    glow_r = int(height * 0.08)
    draw.ellipse([candle_cx - glow_r, candle_cy - glow_r, candle_cx + glow_r, candle_cy + glow_r], fill=glow_color)

    # Base and bottom finial droplet
    draw.line([(cx - body_w_base, body_bottom), (cx + body_w_base, body_bottom)], fill=body_color, width=2)
    finial_h = int(height * 0.10)
    draw.polygon([
        (cx - 4, body_bottom),
        (cx + 4, body_bottom),
        (cx, body_bottom + finial_h),
    ], fill=body_color)

def draw_mosque_silhouette(draw: ImageDraw.ImageDraw, W: int, base_y: int, fill_color: tuple, accent_color: tuple):
    """Draw a dignified mosque skyline (grand central dome, half-domes, minarets)."""
    # 1. Base roofline
    draw.rectangle([0, base_y, W, base_y + 160], fill=fill_color)

    cx = W // 2

    # 2. Grand Central Dome (half ellipse + pointed tip)
    dome_w = 260
    dome_h = 180
    dome_top = base_y - dome_h
    draw.pieslice([cx - dome_w // 2, dome_top, cx + dome_w // 2, base_y + dome_h], 180, 360, fill=fill_color)
    # Pointed finial + small crescent
    draw.line([(cx, dome_top - 30), (cx, dome_top)], fill=accent_color, width=3)
    draw.ellipse([cx - 8, dome_top - 46, cx + 8, dome_top - 30], outline=accent_color, width=2)

    # 3. Flanking half-domes
    for offset in (-180, 180):
        sd_cx = cx + offset
        sd_w = 140
        sd_h = 95
        sd_top = base_y - sd_h
        draw.pieslice([sd_cx - sd_w // 2, sd_top, sd_cx + sd_w // 2, base_y + sd_h], 180, 360, fill=fill_color)
        draw.line([(sd_cx, sd_top - 18), (sd_cx, sd_top)], fill=accent_color, width=2)

    # 4. Two Slender Minarets (left and right)
    for m_cx in (130, W - 130):
        m_w = 34
        m_h = 360
        m_top = base_y - m_h
        # Shaft
        draw.rectangle([m_cx - m_w // 2, m_top + 60, m_cx + m_w // 2, base_y], fill=fill_color)
        # Lower & Upper Balconies
        draw.rectangle([m_cx - m_w // 2 - 8, m_top + 160, m_cx + m_w // 2 + 8, m_top + 172], fill=accent_color)
        draw.rectangle([m_cx - m_w // 2 - 6, m_top + 60, m_cx + m_w // 2 + 6, m_top + 70], fill=accent_color)
        # Conical Spire
        draw.polygon([
            (m_cx - m_w // 2, m_top + 60),
            (m_cx, m_top),
            (m_cx + m_w // 2, m_top + 60),
        ], fill=fill_color)
        draw.line([(m_cx, m_top - 20), (m_cx, m_top)], fill=accent_color, width=2)

def draw_nature_mountains(draw: ImageDraw.ImageDraw, W: int, base_y: int,
                          color_far: tuple, color_near: tuple):
    """Draw layered peaceful mountain silhouettes."""
    # Far ridge
    pts_far = [(0, base_y + 100)]
    far_peaks = [
        (0, base_y - 80), (200, base_y - 180), (450, base_y - 110),
        (700, base_y - 210), (920, base_y - 120), (W, base_y - 160)
    ]
    for p in far_peaks:
        pts_far.append(p)
    pts_far.extend([(W, base_y + 200), (0, base_y + 200)])
    draw.polygon(pts_far, fill=color_far)

    # Near ridge
    pts_near = [(0, base_y + 100)]
    near_peaks = [
        (0, base_y - 40), (280, base_y - 130), (520, base_y - 60),
        (800, base_y - 150), (W, base_y - 70)
    ]
    for p in near_peaks:
        pts_near.append(p)
    pts_near.extend([(W, base_y + 200), (0, base_y + 200)])
    draw.polygon(pts_near, fill=color_near)

def draw_celestial_stars(draw: ImageDraw.ImageDraw, W: int, max_y: int, count: int, color: tuple):
    """Draw subtle twinkling celestial stars in upper canvas."""
    import random
    rng = random.Random(42)  # Deterministic seed for aesthetic consistency
    for _ in range(count):
        sx = rng.randint(60, W - 60)
        sy = rng.randint(80, max_y)
        size = rng.choice([1, 2, 2, 3])
        if size == 3:
            # Diamond twinkle
            draw.polygon([(sx, sy - 3), (sx + 3, sy), (sx, sy + 3), (sx - 3, sy)], fill=color)
        else:
            draw.ellipse([sx - size, sy - size, sx + size, sy + size], fill=color)

# ─────────────────────────────────────────────
# MASTER THEMED BACKGROUND GENERATOR
# ─────────────────────────────────────────────

def render_themed_background(theme: Dict[str, Any], W: int = 1080, H: int = 1920) -> Image.Image:
    """
    Generate a full 1080x1920 themed canvas with smooth gradients
    and curated procedural Islamic artwork.
    """
    top_c = theme["bg_top"]
    bot_c = theme["bg_bottom"]
    gold = theme["gold"]
    gold_dim = theme["gold_dim"]
    style = theme.get("style", "midnight_gold")

    # 1. Base Vertical Gradient
    img = Image.new("RGB", (W, H), top_c)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        ratio = y / float(H)
        r = int(top_c[0] * (1.0 - ratio) + bot_c[0] * ratio)
        g = int(top_c[1] * (1.0 - ratio) + bot_c[1] * ratio)
        b = int(top_c[2] * (1.0 - ratio) + bot_c[2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    cx = W // 2

    # 2. Atmospheric Radial Glow
    glow_c = theme.get("glow", gold)
    for r in range(500, 0, -12):
        ratio = (1.0 - r / 500.0) ** 2
        alpha_factor = 0.08 if theme.get("is_light") else 0.14
        c = tuple(
            int(top_c[i] + (glow_c[i] - top_c[i]) * ratio * alpha_factor)
            for i in range(3)
        )
        draw.ellipse([cx - r, H // 3 - r // 2, cx + r, H // 3 + r // 2], fill=c)

    # 3. Theme-Specific Islamic Decor
    if style == "midnight_gold":
        # Double gold border with 8-pointed star crests
        p = 46
        draw.rectangle([p, p, W - p, H - p], outline=gold_dim, width=1)
        draw.rectangle([p + 14, p + 14, W - p - 14, H - p - 14], outline=gold_dim, width=1)
        draw_8point_star(draw, cx, p + 7, 18, 10, gold, outline_color=gold_dim)
        draw_8point_star(draw, cx, H - p - 7, 18, 10, gold, outline_color=gold_dim)

    elif style == "emerald_serenity":
        # Pointed Moorish arch frame
        p = 46
        draw.rectangle([p, p + 160, W - p, H - p], outline=gold_dim, width=1)
        # Arch top
        arch_pts = [
            (p, p + 160),
            (p + 60, p + 60),
            (cx, p + 10),
            (W - p - 60, p + 60),
            (W - p, p + 160),
        ]
        draw.line(arch_pts, fill=gold_dim, width=2)
        draw_8point_star(draw, cx, p + 40, 16, 9, gold)

    elif style == "minimal_white":
        # Refined single hairline frame with corner accents
        p = 50
        draw.rectangle([p, p, W - p, H - p], outline=gold_dim, width=1)
        # Corner brackets
        corner_len = 30
        for x, y, dx, dy in [
            (p, p, 1, 1), (W - p, p, -1, 1),
            (p, H - p, 1, -1), (W - p, H - p, -1, -1)
        ]:
            draw.line([(x, y + dy * corner_len), (x, y), (x + dx * corner_len, y)], fill=gold, width=2)

    elif style == "peaceful-nature" or style == "peaceful_nature":
        # Misty mountains along bottom
        far_c = (int(bot_c[0] * 1.5), int(bot_c[1] * 1.5), int(bot_c[2] * 1.5))
        near_c = (int(bot_c[0] * 1.2), int(bot_c[1] * 1.2), int(bot_c[2] * 1.2))
        draw_nature_mountains(draw, W, H - 280, far_c, near_c)
        p = 46
        draw.rectangle([p, p, W - p, H - p], outline=gold_dim, width=1)

    elif style == "reflective_night":
        # Stars in celestial sky
        draw_celestial_stars(draw, W, 700, 38, theme["accent"])
        # Radiant crescent moon in upper right quadrant
        draw_crescent_moon(draw, W - 180, 180, 48, gold, top_c, offset_x=16)
        p = 46
        draw.rectangle([p, p, W - p, H - p], outline=gold_dim, width=1)

    elif style == "masjid_elegance":
        # Grand mosque silhouette along bottom
        dome_color = (int(bot_c[0] * 0.7), int(bot_c[1] * 0.7), int(bot_c[2] * 0.7))
        draw_mosque_silhouette(draw, W, H - 220, dome_color, gold_dim)
        p = 46
        draw.rectangle([p, p, W - p, H - 200], outline=gold_dim, width=1)

    elif style == "ramadan_eid":
        # Hanging decorative lanterns (left and right)
        draw_hanging_lantern(draw, 140, 46, 260, gold, (255, 200, 80))
        draw_hanging_lantern(draw, W - 140, 46, 260, gold, (255, 200, 80))
        draw_hanging_lantern(draw, cx, 46, 190, gold_dim, (255, 220, 120))
        # Crescent star in upper sky
        draw_crescent_moon(draw, cx, 290, 36, gold, top_c, offset_x=12)
        p = 46
        draw.rectangle([p, p, W - p, H - p], outline=gold_dim, width=1)

    return img
