from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 225
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 96)
reg  = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)

blue = (24, 144, 255, 255)
navy = (8, 28, 51, 255)
gray = (110, 120, 135, 220)

x = 8
y = 20
draw.text((x, y), "BCS", font=bold, fill=blue)
bcs_w = draw.textlength("BCS", font=bold)
draw.text((x + bcs_w, y), " BEAM", font=bold, fill=navy)

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
img.save(r"C:\My Software Dev\BCS BEAM\flutter\assets\logo.png")
print("saved")
