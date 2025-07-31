import io
import random
import unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import emoji

RESOURCE_DIR: Path = Path(__file__).resolve().parent / "resource"
FONT_PATH: Path = RESOURCE_DIR / "jyhphy-2.ttf"
EMOJI_FONT_PATH: Path = RESOURCE_DIR / "EmojiOneColor.otf"

FONT_SIZE = 32  # 字体大小
TEXT_PADDING = 20  # 文本与边框的间距
AVATAR_RATIO = 0.6  # 头像宽度占图片宽度的比例
BORDER_THICKNESS = 12  # 边框厚度
BORDER_COLOR_RANGE = (64, 255)  # 边框颜色范围
CORNER_RADIUS = 60  # 圆角大小
LINE_SPACING = 36  # 行间距
MIN_AVATAR_SIZE = 80  # 头像最小尺寸
MAX_AVATAR_SIZE = 200  # 头像最大尺寸

cute_font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
emoji_font = ImageFont.truetype(EMOJI_FONT_PATH, FONT_SIZE)

def create_image(avatar: bytes, reply: list) -> bytes:
    reply_str = "\n".join(reply)
    # 创建临时图片计算文本的宽高
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # 计算行数和最大宽度
    lines = reply_str.split("\n")
    line_count = len(lines)
    
    # 计算最大行宽
    max_line_width = 0
    for line in lines:
        line_width = 0
        for char in line:
            if emoji.is_emoji(char):
                bbox = emoji_font.getbbox(char)
                char_width = bbox[2] - bbox[0]
            elif unicodedata.category(char)[0] in ["C", "Z"]:
                char_width = cute_font.getlength(" ")
            else:
                bbox = cute_font.getbbox(char)
                char_width = bbox[2] - bbox[0]
            line_width += char_width
        if line_width > max_line_width:
            max_line_width = line_width
    
    # 计算文本区域高度
    text_height = line_count * LINE_SPACING
    
    # 步骤1: 计算图片宽度（基于文本宽度）
    img_width = int(max_line_width + 2 * TEXT_PADDING)
    
    # 步骤2: 基于图片宽度计算头像大小
    avatar_size = int(img_width * AVATAR_RATIO)
    # 确保头像在合理范围内
    avatar_size = max(MIN_AVATAR_SIZE, min(avatar_size, MAX_AVATAR_SIZE))
    
    # 步骤3: 调整图片宽度（确保能容纳头像）
    img_width = max(img_width, avatar_size + 2 * TEXT_PADDING)
    
    # 计算图片总高度
    img_height = avatar_size + text_height + 3 * TEXT_PADDING  # 头像上方+头像下方+文本下方
    
    # 创建主图像
    img = Image.new("RGBA", (img_width, img_height), color=(255, 255, 255, 255))
    
    # 处理头像
    avatar_img = Image.open(BytesIO(avatar))
    avatar_img = avatar_img.resize((avatar_size, avatar_size))
    
    # 处理头像圆角
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [(0, 0), (avatar_size, avatar_size)], CORNER_RADIUS, fill=255
    )
    avatar_img.putalpha(mask)
    
    # 放置头像（水平居中）
    avatar_x = (img_width - avatar_size) // 2
    img.paste(avatar_img, (avatar_x, TEXT_PADDING), mask)
    
    # 绘制文本（水平居中）
    text_x = (img_width - max_line_width) // 2
    text_y = avatar_size + 2 * TEXT_PADDING
    _draw_multi(img, reply_str, text_x, text_y)
    
    # 绘制边框
    border_color = (
        random.randint(*BORDER_COLOR_RANGE),
        random.randint(*BORDER_COLOR_RANGE),
        random.randint(*BORDER_COLOR_RANGE),
    )
    border_img = Image.new(
        mode="RGBA",
        size=(img_width + BORDER_THICKNESS * 2, img_height + BORDER_THICKNESS * 2),
        color=border_color,
    )
    border_img.paste(img, (BORDER_THICKNESS, BORDER_THICKNESS))

    img_byte_arr = io.BytesIO()
    border_img.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()

def _draw_multi(img, text, text_x=10, text_y=10):
    """
    在图片上绘制多语言文本（支持所有Unicode字符）
    """
    lines = text.split("\n")
    current_y = text_y
    draw = ImageDraw.Draw(img)

    for line in lines:
        line_color = (
            random.randint(0, 128),
            random.randint(0, 128),
            random.randint(0, 128),
            random.randint(240, 255),
        )
        current_x = text_x
        for char in line:
            # 跳过控制字符（不渲染）
            if unicodedata.category(char)[0] == "C" and char != "\n":
                continue
                
            if emoji.is_emoji(char):
                # 绘制emoji字符
                draw.text((current_x, current_y + 5), char, font=emoji_font, fill=line_color)
                bbox = emoji_font.getbbox(char)
                char_width = bbox[2] - bbox[0]
            elif unicodedata.category(char)[0] in ["Z", "C"]:
                # 处理空白字符和控制字符
                char_width = cute_font.getlength(" ")
            else:
                # 绘制普通字符
                draw.text((current_x, current_y), char, font=cute_font, fill=line_color)
                bbox = cute_font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                
            current_x += char_width
        current_y += LINE_SPACING
    return img