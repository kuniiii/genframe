from inky.auto import auto
# from inky import InkyWHAT, InkyWHAT_SSD1683
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne

inky_display = auto(ask_user=True, verbose=True)
# inky_display = InkyWHAT("black")
# inky_display.WIDTH = 400
# inky_display.HEIGHT = 300
inky_display.set_border(inky_display.WHITE)
print(inky_display)


font = ImageFont.truetype(FredokaOne, 36)


img = Image.new("P", (inky_display.width, inky_display.height))
draw = ImageDraw.Draw(img)


message = "Hello there you!"
w, h = font.getsize(message)
x = (inky_display.width / 2) - (w / 2)
y = (inky_display.height / 2) - (h / 2)

draw.text((x, y), message, inky_display.BLACK, font)
inky_display.set_image(img)
inky_display.show()