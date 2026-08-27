from PIL import Image, ImageDraw, ImageFont

# BCS Beam mac tray icons (2026-08-26): replace the stock RustDesk swirl still
# sitting in res/mac-tray-{dark,light}-x2.png. Design matches the already-
# approved Windows tray icon (res/tray-icon.ico): bold "B" inside a rounded-
# square outline, monochrome. macOS menu-bar convention: "dark" variant =
# black glyph (for light menu bar), "light" variant = white glyph (for dark
# menu bar). Rendered at 4x then downsampled for clean edges. Output sizes
# match the existing files exactly (60x60 dark, 48x48 light) so they're
# drop-in replacements for whatever the build scripts expect.

SCRATCH = r"C:\Users\ZHANGJ~1\AppData\Local\Temp\claude\C--My-Software-Dev-BCS-BEAM\91af5377-1684-4441-8d86-901df7de77c7\scratchpad"

def make_tray(size, color, out_path):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # rounded-square outline, mirroring tray-icon.ico's look
    margin = s // 12
    stroke = max(s // 16, 4)
    radius = s // 5
    draw.rounded_rectangle(
        [margin, margin, s - margin, s - margin],
        radius=radius, outline=color, width=stroke)
    # bold "B" centered
    font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", int(s * 0.58))
    bbox = draw.textbbox((0, 0), "B", font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((s - w) / 2 - bbox[0], (s - h) / 2 - bbox[1]), "B",
              font=font, fill=color)
    img = img.resize((size, size), Image.LANCZOS)
    img.save(out_path)
    print("saved", out_path, img.size)

make_tray(60, (0, 0, 0, 255), SCRATCH + r"\mac-tray-dark-x2.png")
make_tray(48, (255, 255, 255, 255), SCRATCH + r"\mac-tray-light-x2.png")
