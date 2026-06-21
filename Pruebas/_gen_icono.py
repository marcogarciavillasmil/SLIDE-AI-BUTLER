from PIL import Image, ImageDraw, ImageFilter
import math

S = 1024
AQ = (0, 229, 204)          # aqua de AIDEN
BG = (6, 13, 15, 255)       # fondo oscuro del shell

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Fondo redondeado tipo "tile" de app
bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(bg).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.20), fill=BG)
img = Image.alpha_composite(img, bg)

cx, cy = S // 2, S // 2

# Resplandor (glow) aqua difuso detras del orbe
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for i in range(60, 0, -1):
    rad = int(S * 0.32 * i / 60)
    a = int(80 * (i / 60) ** 2)
    gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(AQ[0], AQ[1], AQ[2], a))
glow = glow.filter(ImageFilter.GaussianBlur(S * 0.035))
img = Image.alpha_composite(img, glow)

d = ImageDraw.Draw(img)

# Anillos concentricos (HUD)
for k, rr in enumerate([0.24, 0.33, 0.43]):
    rad = int(S * rr)
    w = max(2, int(S * 0.007 * (1 - k * 0.18)))
    a = int(200 - k * 55)
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(AQ[0], AQ[1], AQ[2], a), width=w)

# Puntos sobre el anillo medio (la "esfera de puntos")
rad = int(S * 0.33)
for j in range(12):
    ang = j * (2 * math.pi / 12) - math.pi / 2
    x = cx + int(math.cos(ang) * rad)
    y = cy + int(math.sin(ang) * rad)
    dr = int(S * 0.013)
    d.ellipse([x - dr, y - dr, x + dr, y + dr], fill=(AQ[0], AQ[1], AQ[2], 255))

# Orbe central
core_r = int(S * 0.15)
d.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r], fill=(AQ[0], AQ[1], AQ[2], 255))
# Brillo del orbe (parte superior mas clara)
hr = int(core_r * 0.55)
d.ellipse([cx - hr, cy - int(core_r * 0.7), cx + hr, cy + int(core_r * 0.1)],
          fill=(200, 255, 248, 170))

# Guardar ICO (varios tamaños) + un PNG de previsualizacion
img.save("AIDEN.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.resize((256, 256), Image.LANCZOS).save("_preview_icono.png")
print("Listo: AIDEN.ico + _preview_icono.png")
