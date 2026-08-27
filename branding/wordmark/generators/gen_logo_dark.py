from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 225
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 96)
reg  = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)

# BCS Beam local-build fix (2026-08-25): dark-mode variant of the sidebar
# wordmark. The light-mode logo.png uses near-black "#081c33" for "BEAM",
# which disappears against a dark-mode sidebar background (both are near-
# black) -- Jack confirmed this by eye on a real dark-mode Windows install.
# Swap "BEAM" to white/near-white and lighten the subtitle for contrast
# against a dark background; keep "BCS" the same brand blue (already has
# enough contrast on both light and dark).
blue = (24, 144, 255, 255)       # #1890ff - same as light variant
light = (240, 245, 250, 255)     # near-white, for "BEAM" on dark bg
gray = (170, 180, 195, 220)      # lighter gray subtitle, for dark bg

x = 8
y = 20
draw.text((x, y), "BCS", font=bold, fill=blue)
bcs_w = draw.textlength("BCS", font=bold)
draw.text((x + bcs_w, y), " BEAM", font=bold, fill=light)

draw.rectangle([x, y + 118, x + 120, y + 124], fill=blue)
draw.text((x, y + 134), "B R O C E N T   C L O U D   S E R V I C E", font=reg, fill=gray)

bbox = img.getbbox()
pad = 6
left, top, right, bottom = bbox
left = max(0, left - pad)
top = max(0, top - pad)
right = min(W, right + pad)
bottom = min(H, bottom + pad)
img = img.crop((left, top, right, bottom))
print("cropped size", img.size)
img.save(r"C:\My Software Dev\BCS BEAM\flutter\assets\logo_dark.png")
print("saved")
