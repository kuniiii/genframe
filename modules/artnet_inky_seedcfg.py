# loading inky stuff
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import textwrap
from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansPro

# setup inky
inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.WHITE)


# Define fonts
title_font = ImageFont.truetype(SourceSerifProSemibold, 24)  # for title
author_font = ImageFont.truetype(SourceSansPro, 20, layout_engine=ImageFont.LAYOUT_BASIC)  # for seed and cfg, a bit smaller
# font = ImageFont.truetype(SourceSerifProSemibold, 24)

def inky_refresh(text: str, max_width: int, seed: int, cfg: str):
    img = Image.new("P", (inky_display.width, inky_display.height))
    draw = ImageDraw.Draw(img)

#   Wrap text for title
    title_lines = textwrap.wrap(text, width=max_width)
    title_message = '\n'.join(title_lines)
    seed_message = "Seed: " + str(seed)
    cfg_message = "Guidance: " + str(cfg)

# Calculate position for title
    title_w, title_h = draw.textsize(title_message, title_font)
    title_x = (inky_display.width / 2) - (title_w / 2)
    title_y = (inky_display.height / 2) - (title_h / 2) - 40

#   Calculate position for seed and cfg, placing them 10px under the title
    seed_h = 20
    seed_x = title_x  # align to the title's left side
    seed_y = title_y + title_h + 70 # 10 pixels below the title

    cfg_x = title_x  # align to the title's left side
    cfg_y = seed_y + seed_h # right below the seed

#   Draw title, seed and cfg
    draw.text((title_x, title_y), title_message, inky_display.BLACK, title_font)
    draw.text((seed_x, seed_y), seed_message, inky_display.BLACK, author_font)
    draw.text((cfg_x, cfg_y), cfg_message, inky_display.BLACK, author_font)

    inky_display.set_image(img)
    inky_display.show()

# def inky_refresh(text: str, max_width: int, seed: int, cfg: str):
#     img = Image.new("P", (inky_display.width, inky_display.height))
#     draw = ImageDraw.Draw(img)
#     print("seed:", seed)
#     print("cfg:", cfg)

#     Wrap text for title, seed and cfg
#     title_lines = textwrap.wrap(text, width=max_width)
#     title_message = '\n'.join(title_lines)

#     seed_message = "Seed: " + str(seed)
#     cfg_message = "Guidance: " + str(cfg)

#     Calculate position for title
#     title_w, title_h = draw.textsize(title_message, title_font)
#     title_x = (inky_display.width / 2) - (title_w / 2)
#     title_y = (inky_display.height / 2) - (title_h / 2)

#     Calculate position for seed and cfg, placing them at the bottom
#     seed_w, seed_h = draw.textsize(seed_message, author_font)
#     seed_x = 10  # a bit of margin from the left
#     seed_y = inky_display.height - seed_h - 10  # 10 pixels above the bottom

#     cfg_w, cfg_h = draw.textsize(cfg_message, author_font)
#     cfg_x = inky_display.width - cfg_w - 10  # a bit of margin from the right
#     cfg_y = inky_display.height - cfg_h - 10  # 10 pixels above the bottom

#     Draw title, seed and cfg
#     draw.text((title_x, title_y), title_message, inky_display.BLACK, title_font)
#     draw.text((seed_x, seed_y), seed_message, inky_display.BLACK, author_font)
#     draw.text((cfg_x, cfg_y), cfg_message, inky_display.BLACK, author_font)

#     inky_display.set_image(img)
#     inky_display.show()