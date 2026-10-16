"""Create four original geometric demo images, never ingest personal or curated artwork."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / 'public-assets/items'


def flower(draw, x, y, radius, pink=False):
    color = '#ed9abb' if pink else '#f8ce62'
    for i in range(8):
        angle = i * math.pi / 4
        cx, cy = x + math.cos(angle) * radius, y + math.sin(angle) * radius
        draw.ellipse((cx-radius*.65, cy-radius*.65, cx+radius*.65, cy+radius*.65), fill=color)
    draw.ellipse((x-radius*.62, y-radius*.62, x+radius*.62, y+radius*.62), fill='#a26847')


def create(asset_id, name, category, tags, size, painter):
    folder = ROOT / asset_id
    folder.mkdir(parents=True, exist_ok=False)
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    painter(ImageDraw.Draw(im), size)
    im.save(folder / 'original.png')
    info = {
        'id': asset_id, 'name': name, 'category': category, 'tags': ['demo'] + tags,
        'aliases': ['placeholder'], 'author': '热拉公共资源（程序生成示例）',
        'source_url': f'https://github.com/Show-o4210/DIY-IMG/tree/main/public-assets/items/{asset_id}',
        'usage': '程序绘制的几何占位示例，允许在本工具中使用、修改和分享；不代表其他素材的使用范围。',
        'description': '占位示例：仅用于体验分区、标签、预览和下载入库，后续可由维护者下架。',
        'file': 'original.png'
    }
    (folder / 'info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def subject(draw, size):
    draw.rounded_rectangle((242, 225, 270, 600), radius=14, fill='#79b26a')
    draw.ellipse((120, 350, 255, 420), fill='#8ac176')
    draw.ellipse((260, 430, 405, 500), fill='#6fa45e')
    flower(draw, 256, 220, 105)


def pattern(draw, size):
    for x, y in [(0, 0), (384, 0), (0, 384), (384, 384), (192, 192)]:
        flower(draw, x, y, 34, True)


def sticker(draw, size):
    flower(draw, 128, 128, 68)


def background(draw, size):
    width, height = size
    for y in range(height):
        draw.line((0, y, width, y), fill=(36 + y * 12 // height, 29 + y * 15 // height, 66 + y * 28 // height, 255))
    for i in range(25):
        x, y = (i * 137 + 71) % width, (i * 229 + 91) % height
        draw.ellipse((x-3, y-3, x+3, y+3), fill='#eddca9')


if __name__ == '__main__':
    create('subject-demo-flower', '占位示例·花朵主体', 'SUBJECT', ['flower', 'plant', 'yellow'], (512, 640), subject)
    create('pattern-demo-flower', '占位示例·花朵图案', 'PATTERN', ['flower', 'pink', 'tile'], (384, 384), pattern)
    create('sticker-demo-flower', '占位示例·花朵贴纸', 'STICKER', ['flower', 'yellow'], (256, 256), sticker)
    create('background-demo-stars', '占位示例·星空底图', 'BACKGROUND', ['star'], (600, 1000), background)
    print('Created four clearly labeled demo materials')
