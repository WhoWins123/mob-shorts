"""
Original blocky cartoon characters (chibi style: big square head, small body) drawn with PIL.
The main character is always W: purple hoodie with a big W on the chest and a black cap.
"""
import math

from PIL import ImageDraw

# role -> look. Colors are (r, g, b).
LOOKS = {
    "W":       dict(skin=(242, 200, 160), hair=(40, 30, 25), style="cap", cap=(25, 25, 30), shirt=(130, 70, 220),
                    pants=(40, 45, 70), shoes=(245, 245, 245), logo="W"),
    "mom":     dict(skin=(236, 190, 150), hair=(120, 70, 35), style="long", shirt=(235, 110, 150), pants=(60, 80, 140),
                    shoes=(90, 50, 40)),
    "dad":     dict(skin=(225, 180, 140), hair=(60, 45, 30), style="short", shirt=(70, 130, 200), pants=(70, 70, 75),
                    shoes=(50, 40, 35), extra="mustache"),
    "kid":     dict(skin=(250, 210, 175), hair=(230, 180, 60), style="spiky", shirt=(250, 170, 40), pants=(70, 110, 200),
                    shoes=(220, 60, 60), size=0.82),
    "girl":    dict(skin=(245, 205, 170), hair=(200, 80, 50), style="pigtails", shirt=(90, 200, 160), pants=(240, 240, 250),
                    shoes=(240, 120, 160), extra="bow"),
    "boy":     dict(skin=(200, 150, 110), hair=(30, 25, 25), style="spiky", shirt=(230, 70, 60), pants=(40, 40, 60),
                    shoes=(240, 240, 240)),
    "friend":  dict(skin=(160, 110, 80), hair=(25, 20, 20), style="short", shirt=(60, 190, 90), pants=(60, 60, 90),
                    shoes=(240, 200, 60), extra="glasses"),
    "teacher": dict(skin=(235, 195, 160), hair=(150, 150, 155), style="bun", shirt=(150, 110, 80), pants=(60, 50, 45),
                    shoes=(40, 30, 30), extra="glasses"),
    "bully":   dict(skin=(230, 185, 145), hair=(220, 60, 40), style="mohawk", shirt=(35, 35, 40), pants=(90, 60, 50),
                    shoes=(30, 30, 30), extra="scar"),
    "rival":   dict(skin=(240, 200, 165), hair=(240, 240, 245), style="spiky", shirt=(220, 50, 70), pants=(30, 30, 40),
                    shoes=(30, 30, 30)),
    "old":     dict(skin=(225, 185, 155), hair=(235, 235, 235), style="bald", shirt=(140, 120, 90), pants=(90, 80, 70),
                    shoes=(60, 45, 35), extra="beard"),
    "doctor":  dict(skin=(215, 170, 130), hair=(50, 40, 30), style="short", shirt=(245, 245, 250), pants=(80, 160, 170),
                    shoes=(240, 240, 240), extra="glasses"),
    "boss":    dict(skin=(230, 190, 150), hair=(35, 30, 30), style="slick", shirt=(45, 45, 55), pants=(45, 45, 55),
                    shoes=(20, 20, 20), extra="tie"),
    "cop":     dict(skin=(205, 160, 120), hair=(30, 25, 20), style="cap", cap=(30, 50, 110), shirt=(40, 70, 150),
                    pants=(30, 40, 80), shoes=(20, 20, 20), logo="*"),
    "king":    dict(skin=(235, 195, 160), hair=(120, 80, 40), style="short", shirt=(170, 30, 50), pants=(120, 20, 40),
                    shoes=(220, 180, 50), extra="crown"),
    "alien":   dict(skin=(120, 220, 120), hair=(120, 220, 120), style="antenna", shirt=(150, 150, 170), pants=(110, 110, 130),
                    shoes=(80, 80, 100)),
    "ghost":   dict(skin=(235, 240, 255), hair=(235, 240, 255), style="bald", shirt=(235, 240, 255), pants=(235, 240, 255),
                    shoes=(235, 240, 255), ghost=True),
    "robot":   dict(skin=(170, 180, 195), hair=(170, 180, 195), style="antenna", shirt=(120, 130, 150),
                    pants=(100, 110, 125), shoes=(80, 85, 95), robot=True),
}

# extra people for "crowd"
CROWD = ["boy", "girl", "friend", "dad", "mom", "kid"]

OUTLINE = (20, 20, 25)


def _darker(c, k=0.75):
    return tuple(int(v * k) for v in c)


def draw_character(img, role, cx, feet_y, scale, expr="neutral", t=0.0, alpha_ghost=150):
    """Draws one character standing with feet at (cx, feet_y)."""
    look = LOOKS.get(role, LOOKS["friend"])
    s = scale * look.get("size", 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    ow = max(2, int(4 * s))

    def R(x0, y0, x1, y1, fill, r=0):
        box = [cx + x0 * s, feet_y + y0 * s, cx + x1 * s, feet_y + y1 * s]
        if look.get("ghost"):
            fill = fill + (alpha_ghost,)
        if r:
            d.rounded_rectangle(box, radius=r * s, fill=fill, outline=OUTLINE, width=ow)
        else:
            d.rectangle(box, fill=fill, outline=OUTLINE, width=ow)

    # body (y goes up from the feet: negative numbers)
    if not look.get("ghost"):
        R(-30, -16, -2, 0, look["shoes"], 4)
        R(2, -16, 30, 0, look["shoes"], 4)
        R(-28, -66, -3, -12, look["pants"])
        R(3, -66, 28, -12, look["pants"])
    else:  # wavy ghost tail instead of legs
        pts = [(cx - 34 * s, feet_y - 70 * s)]
        for i in range(7):
            pts.append((cx + (-34 + i * 11.3) * s, feet_y - (6 if i % 2 else 18) * s + math.sin(t * 6 + i) * 3 * s))
        pts.append((cx + 34 * s, feet_y - 70 * s))
        d.polygon(pts, fill=look["shirt"] + (alpha_ghost,), outline=OUTLINE)

    # arms (wave a little)
    swing = math.sin(t * 5) * 3
    arm_y = -136
    R(-52, arm_y + swing, -32, arm_y + 62 + swing, look["shirt"], 6)
    R(-52, arm_y + 40 + swing, -32, arm_y + 64 + swing, look["skin"], 6)
    R(32, arm_y - swing, 52, arm_y + 62 - swing, look["shirt"], 6)
    R(32, arm_y + 40 - swing, 52, arm_y + 64 - swing, look["skin"], 6)
    # torso
    R(-34, -140, 34, -62, look["shirt"], 8)
    if look.get("logo"):
        from .text import font
        f = font(int(44 * s))
        d.text((cx, feet_y - 102 * s), look["logo"], font=f, fill=(255, 255, 255), anchor="mm",
               stroke_width=max(2, int(3 * s)), stroke_fill=OUTLINE)
    if look.get("extra") == "tie":
        d.polygon([(cx, feet_y - 138 * s), (cx - 7 * s, feet_y - 110 * s), (cx, feet_y - 80 * s),
                   (cx + 7 * s, feet_y - 110 * s)], fill=(200, 30, 40), outline=OUTLINE)
    if look.get("robot"):
        for i in range(3):
            d.ellipse([cx - 22 * s + i * 16 * s, feet_y - 112 * s, cx - 12 * s + i * 16 * s, feet_y - 102 * s],
                      fill=[(240, 60, 60), (60, 220, 90), (60, 140, 240)][i])

    # head (big and boxy)
    hx0, hy0, hx1, hy1 = -46, -228, 46, -136
    R(hx0, hy0, hx1, hy1, look["skin"], 14)
    _hair(d, look, cx, feet_y, s, ow)
    _face(d, look, cx, feet_y, s, expr, t)
    _extras(d, look, cx, feet_y, s, ow)


def _hair(d, look, cx, fy, s, ow):
    c = look["hair"]
    style = look["style"]

    def P(points):
        d.polygon([(cx + x * s, fy + y * s) for x, y in points], fill=c, outline=OUTLINE)

    if style == "cap":
        cap = look.get("cap", (30, 30, 30))
        d.rounded_rectangle([cx - 50 * s, fy - 240 * s, cx + 50 * s, fy - 200 * s], radius=14 * s, fill=cap,
                            outline=OUTLINE, width=ow)
        d.rounded_rectangle([cx - 4 * s, fy - 214 * s, cx + 72 * s, fy - 200 * s], radius=6 * s, fill=cap,
                            outline=OUTLINE, width=ow)
    elif style == "short":
        d.rounded_rectangle([cx - 48 * s, fy - 236 * s, cx + 48 * s, fy - 204 * s], radius=12 * s, fill=c,
                            outline=OUTLINE, width=ow)
    elif style == "slick":
        P([(-48, -206), (-48, -230), (-20, -240), (40, -238), (50, -222), (10, -214), (-30, -212)])
    elif style == "spiky":
        P([(-50, -204), (-46, -236), (-34, -250), (-22, -236), (-8, -256), (6, -236), (20, -254), (32, -236),
           (46, -248), (50, -204), (20, -214), (-20, -214)])
    elif style == "mohawk":
        P([(-12, -224), (-14, -262), (0, -272), (14, -262), (12, -224)])
    elif style == "long":
        d.rounded_rectangle([cx - 54 * s, fy - 238 * s, cx + 54 * s, fy - 120 * s], radius=20 * s, fill=c,
                            outline=OUTLINE, width=ow)
        d.rounded_rectangle([cx - 40 * s, fy - 214 * s, cx + 40 * s, fy - 136 * s], radius=10 * s, fill=look["skin"])
    elif style == "pigtails":
        d.rounded_rectangle([cx - 48 * s, fy - 236 * s, cx + 48 * s, fy - 206 * s], radius=12 * s, fill=c,
                            outline=OUTLINE, width=ow)
        for side in (-1, 1):
            d.ellipse([cx + side * 52 * s - 16 * s, fy - 214 * s, cx + side * 52 * s + 16 * s, fy - 170 * s], fill=c,
                      outline=OUTLINE, width=ow)
    elif style == "bun":
        d.rounded_rectangle([cx - 48 * s, fy - 234 * s, cx + 48 * s, fy - 208 * s], radius=12 * s, fill=c,
                            outline=OUTLINE, width=ow)
        d.ellipse([cx - 20 * s, fy - 266 * s, cx + 20 * s, fy - 230 * s], fill=c, outline=OUTLINE, width=ow)
    elif style == "antenna":
        for side in (-1, 1):
            d.line([cx + side * 22 * s, fy - 226 * s, cx + side * 32 * s, fy - 262 * s], fill=OUTLINE, width=ow)
            d.ellipse([cx + side * 32 * s - 8 * s, fy - 270 * s, cx + side * 32 * s + 8 * s, fy - 254 * s],
                      fill=(255, 230, 80), outline=OUTLINE, width=ow)
    # "bald": nothing


def _face(d, look, cx, fy, s, expr, t):
    ey = fy - 186 * s
    ex = 20 * s
    my = fy - 158 * s
    black = (25, 20, 25)
    w = max(3, int(5 * s))
    if look.get("robot"):
        d.rectangle([cx - 34 * s, ey - 10 * s, cx + 34 * s, ey + 10 * s], fill=(40, 40, 50))
        glow = (255, 60, 60) if expr in ("angry", "shock", "scared") else (80, 220, 255)
        d.rectangle([cx - 28 * s, ey - 4 * s, cx + 28 * s, ey + 4 * s], fill=glow)
        d.line([cx - 16 * s, my, cx + 16 * s, my], fill=black, width=w)
        return

    def eye(x, big=False, heart=False):
        if heart:
            r = 9 * s
            d.ellipse([x - r, ey - r, x, ey], fill=(230, 40, 70))
            d.ellipse([x, ey - r, x + r, ey], fill=(230, 40, 70))
            d.polygon([(x - r, ey - r / 2), (x + r, ey - r / 2), (x, ey + r)], fill=(230, 40, 70))
        elif big:
            d.ellipse([x - 12 * s, ey - 13 * s, x + 12 * s, ey + 13 * s], fill=(255, 255, 255), outline=black, width=w // 2 + 1)
            d.ellipse([x - 5 * s, ey - 5 * s, x + 5 * s, ey + 5 * s], fill=black)
        else:
            blink = (t * 1.3) % 4 < 0.12
            if blink:
                d.line([x - 7 * s, ey, x + 7 * s, ey], fill=black, width=w)
            else:
                d.rounded_rectangle([x - 6 * s, ey - 9 * s, x + 6 * s, ey + 9 * s], radius=5 * s, fill=black)

    big = expr in ("shock", "scared")
    heart = expr == "love"
    if expr == "happy":
        for x in (cx - ex, cx + ex):
            d.arc([x - 9 * s, ey - 6 * s, x + 9 * s, ey + 10 * s], 200, 340, fill=black, width=w)
    else:
        eye(cx - ex, big, heart)
        eye(cx + ex, big, heart)

    # eyebrows
    if expr in ("angry", "smirk"):
        d.line([cx - ex - 12 * s, ey - 20 * s, cx - ex + 10 * s, ey - 12 * s], fill=black, width=w)
        if expr == "angry":
            d.line([cx + ex + 12 * s, ey - 20 * s, cx + ex - 10 * s, ey - 12 * s], fill=black, width=w)
        else:
            d.line([cx + ex - 10 * s, ey - 20 * s, cx + ex + 12 * s, ey - 22 * s], fill=black, width=w)
    elif expr in ("sad", "cry", "scared"):
        d.line([cx - ex - 12 * s, ey - 14 * s, cx - ex + 10 * s, ey - 22 * s], fill=black, width=w)
        d.line([cx + ex + 12 * s, ey - 14 * s, cx + ex - 10 * s, ey - 22 * s], fill=black, width=w)

    # mouth
    if expr in ("happy", "love"):
        d.chord([cx - 18 * s, my - 14 * s, cx + 18 * s, my + 14 * s], 0, 180, fill=(120, 30, 40), outline=black, width=w // 2 + 1)
    elif expr in ("sad", "cry"):
        d.arc([cx - 16 * s, my - 2 * s, cx + 16 * s, my + 20 * s], 200, 340, fill=black, width=w)
    elif expr == "angry":
        d.rectangle([cx - 16 * s, my - 2 * s, cx + 16 * s, my + 8 * s], fill=(255, 255, 255), outline=black, width=w // 2 + 1)
    elif expr in ("shock", "scared"):
        d.ellipse([cx - 9 * s, my - 8 * s, cx + 9 * s, my + 14 * s], fill=(90, 20, 30), outline=black, width=w // 2 + 1)
    elif expr == "smirk":
        d.arc([cx - 4 * s, my - 14 * s, cx + 22 * s, my + 6 * s], 20, 150, fill=black, width=w)
    else:
        d.line([cx - 12 * s, my + 2 * s, cx + 12 * s, my + 2 * s], fill=black, width=w)

    if expr == "cry":
        for x in (cx - ex, cx + ex):
            drop = (t * 120) % (40 * s)
            d.rounded_rectangle([x - 4 * s, ey + 8 * s, x + 4 * s, ey + 8 * s + drop + 6 * s], radius=4 * s, fill=(90, 170, 255))
    if expr == "scared":
        d.ellipse([cx + 40 * s, ey - 26 * s, cx + 52 * s, ey - 8 * s], fill=(120, 190, 255))
    if expr in ("happy", "love"):
        for x in (cx - 34 * s, cx + 26 * s):
            d.ellipse([x, my - 16 * s, x + 10 * s, my - 8 * s], fill=(255, 130, 140, 160))


def _extras(d, look, cx, fy, s, ow):
    e = look.get("extra")
    black = OUTLINE
    if e == "glasses":
        for x in (cx - 20 * s, cx + 20 * s):
            d.rounded_rectangle([x - 14 * s, fy - 198 * s, x + 14 * s, fy - 174 * s], radius=4 * s, outline=black, width=ow)
        d.line([cx - 6 * s, fy - 188 * s, cx + 6 * s, fy - 188 * s], fill=black, width=ow)
    elif e == "mustache":
        d.rounded_rectangle([cx - 20 * s, fy - 170 * s, cx + 20 * s, fy - 160 * s], radius=5 * s, fill=look["hair"])
    elif e == "beard":
        d.rounded_rectangle([cx - 38 * s, fy - 166 * s, cx + 38 * s, fy - 128 * s], radius=14 * s, fill=look["hair"],
                            outline=black, width=ow)
        d.line([cx - 12 * s, fy - 156 * s, cx + 12 * s, fy - 156 * s], fill=(40, 30, 30), width=ow)
    elif e == "bow":
        d.polygon([(cx + 20 * s, fy - 238 * s), (cx + 44 * s, fy - 250 * s), (cx + 44 * s, fy - 224 * s)],
                  fill=(240, 90, 150), outline=black)
        d.polygon([(cx + 20 * s, fy - 238 * s), (cx - 4 * s, fy - 250 * s), (cx - 4 * s, fy - 224 * s)],
                  fill=(240, 90, 150), outline=black)
    elif e == "scar":
        d.line([cx + 26 * s, fy - 200 * s, cx + 34 * s, fy - 176 * s], fill=(170, 60, 60), width=ow)
    elif e == "crown":
        pts = [(-36, -228), (-36, -262), (-20, -244), (0, -268), (20, -244), (36, -262), (36, -228)]
        d.polygon([(cx + x * s, fy + y * s) for x, y in pts], fill=(250, 200, 40), outline=black)
