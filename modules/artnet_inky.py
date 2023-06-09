# loading inky stuff
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import textwrap
from font_source_serif_pro import SourceSerifProSemibold
# from font_source_sans_pro import SourceSansProSemibold

# setup inky
inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.WHITE)

font = ImageFont.truetype(SourceSerifProSemibold, 24)

# def inky_refresh(text: str, max_width: int, font: ImageFont):
def inky_refresh(text: str, max_width: int):
    img = Image.new("P", (inky_display.width, inky_display.height))
    draw = ImageDraw.Draw(img)

    #wrap text
    lines = textwrap.wrap(text, width=max_width)
    message = '\n'.join(lines)

    w, h = draw.textsize(message, font)
    x = (inky_display.width / 2) - (w / 2)
    y = (inky_display.height / 2) - (h / 2)
    #draw.text((x, y), message, inky_display.BLACK, font)
    draw.multiline_text((x, y), message, inky_display.BLACK, font)

    inky_display.set_image(img)
    inky_display.show()