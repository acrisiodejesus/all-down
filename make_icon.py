import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.makedirs("assets", exist_ok=True)

size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

pad = 28
rect = [pad, pad, size - pad, size - pad]
radius = 110

mask = Image.new("L", (size, size), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.rounded_rectangle(rect, radius=radius, fill=255)

grad = Image.new("RGBA", (size, size))
for y in range(size):
    t = y / size
    r = int(24 + (210 - 24) * (t ** 1.3))
    g = int(24 + (24 - 24) * t)
    b = int(30 + (50 - 30) * (t ** 1.5))
    for x in range(size):
        dx = x - 140
        dy = y - 120
        dist = math.sqrt(dx * dx + dy * dy)
        hl = max(0, 1 - dist / 320) * 45
        grad.putpixel((x, y), (min(255, int(r + hl)), min(255, int(g + hl * 0.4)), min(255, int(b + hl * 0.6)), 255))

img.paste(grad, (0, 0), mask)

border_mask = Image.new("L", (size, size), 0)
b_draw = ImageDraw.Draw(border_mask)
b_draw.rounded_rectangle([pad + 2, pad + 2, size - pad - 2, size - pad - 2], radius=radius - 2, outline=255, width=4)
border_layer = Image.new("RGBA", (size, size), (255, 255, 255, 60))
img.paste(border_layer, (0, 0), border_mask)

shadow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
s_draw = ImageDraw.Draw(shadow_layer)

cx = size // 2
cy = size // 2 - 20

arrow_w = 70
arrow_top = 130
arrow_bot = 270
head_w = 140
head_tip = 350

arrow_points = [
    (cx - arrow_w, arrow_top),
    (cx + arrow_w, arrow_top),
    (cx + arrow_w, arrow_bot),
    (cx + head_w, arrow_bot),
    (cx, head_tip),
    (cx - head_w, arrow_bot),
    (cx - arrow_w, arrow_bot),
]

s_draw.polygon(arrow_points, fill=(0, 0, 0, 140))
s_draw.rounded_rectangle([cx - 150, head_tip + 30, cx + 150, head_tip + 46], radius=8, fill=(0, 0, 0, 140))
shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, shadow_blurred)

draw = ImageDraw.Draw(img)
draw.polygon(arrow_points, fill=(255, 255, 255, 250))

tray_y = head_tip + 30
draw.rounded_rectangle([cx - 140, tray_y, cx + 140, tray_y + 16], radius=8, fill=(255, 255, 255, 240))

badge_x2 = size - pad - 24
badge_y1 = pad + 24
badge_w = 110
badge_h = 44
badge_x1 = badge_x2 - badge_w
badge_y2 = badge_y1 + badge_h

draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=14, fill=(255, 215, 0, 240))
try:
    font = ImageFont.truetype("segoeuib.ttf", 26)
except Exception:
    font = ImageFont.load_default()

text_bbox = draw.textbbox((0, 0), "4K", font=font)
tw = text_bbox[2] - text_bbox[0]
th = text_bbox[3] - text_bbox[1]
tx = badge_x1 + (badge_w - tw) // 2
ty = badge_y1 + (badge_h - th) // 2 - 2
draw.text((tx, ty), "4K", fill=(20, 20, 20, 255), font=font)

png_path = os.path.join("assets", "icon.png")
img.save(png_path, "PNG")

ico_path = os.path.join("assets", "icon.ico")
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(ico_path, format="ICO", sizes=sizes)
