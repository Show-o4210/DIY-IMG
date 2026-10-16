"""Build a public material catalog. Never imports curated works or traverses user libraries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1] / 'public-assets'
CATEGORIES = {'SUBJECT', 'FRAME', 'RIBBON', 'BACKGROUND', 'PATTERN', 'STICKER', 'COST', 'ATTACK', 'HEALTH', 'HERO_TYPE', 'SKILL', 'TEXT_ICON'}
IDENTIFIER = re.compile(r'[A-Za-z0-9._-]{1,80}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def text(value, limit, optional=False):
    require(isinstance(value, str) and (optional or value.strip()) and len(value) <= limit, '文字字段无效')
    require(not any(ord(c) < 32 and c != '\n' for c in value), '文字中包含控制字符')
    return value.strip()


def strings(values):
    require(isinstance(values, list) and len(values) <= 30, '标签 / 别名无效')
    result = [text(x, 80) for x in values]
    require(len(result) == len(set(result)), '标签 / 别名重复')
    return result


def image_spec(data, thumbnail=False):
    require(0 < len(data) <= (1024 * 1024 if thumbnail else 32 * 1024 * 1024), '图片文件过大')
    with Image.open(BytesIO(data)) as im:
        width, height = im.size
        require(0 < width <= 16000 and 0 < height <= 16000 and width * height <= (1_000_000 if thumbnail else 40_000_000), '图片尺寸过大')
        require(im.format in ({'PNG', 'JPEG', 'WEBP'} if thumbnail else {'PNG', 'JPEG'}), '图片格式不支持')
        fmt = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp'}[im.format]
        im.verify()
    digest = hashlib.sha256(data).hexdigest()
    return {'path': f'files/{digest}.{fmt}', 'sha256': digest, 'bytes': len(data), 'width': width, 'height': height, 'format': fmt}


def write_immutable(path, data, build):
    if path.exists():
        require(path.read_bytes() == data, f'不可变文件发生变化：{path.name}')
    elif build:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    else:
        raise ValueError(f'缺少生成文件：{path}; 请先运行 --build')


def compile_catalog(root=ROOT, build=False):
    tags = json.loads((root / 'tags.json').read_text(encoding='utf-8'))
    require(isinstance(tags, list) and len(tags) <= 2000, '标签目录无效')
    tag_ids, labels = set(), set()
    for tag in tags:
        require(IDENTIFIER.fullmatch(tag['id']) and tag['id'] not in tag_ids, '标签 ID 无效或重复')
        tag_ids.add(tag['id'])
        label = text(tag['label'], 40).casefold()
        require(label not in labels and not label.startswith(('#', '＃')), '标签名称重复或包含 #')
        labels.add(label)
        strings(tag.get('aliases', []))
    items, item_ids = [], set()
    item_paths = sorted((root / 'items').glob('*/info.json'))
    require(len(item_paths) <= 10000, '资源过多')
    for path in item_paths:
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), '不允许资源路径跳转')
        info = json.loads(path.read_text(encoding='utf-8'))
        asset_id = info['id']
        require(IDENTIFIER.fullmatch(asset_id) and asset_id not in item_ids and asset_id == path.parent.name, '资源 ID 无效 / 重复 / 与目录不符')
        item_ids.add(asset_id)
        require(info['category'] in CATEGORIES, '资源分区无效')
        strings(info['tags']); require(all(t in tag_ids for t in info['tags']), '引用了未定义标签')
        strings(info.get('aliases', []))
        for key, limit in [('name', 120), ('author', 120), ('usage', 1000)]:
            text(info[key], limit)
        text(info.get('description', ''), 2000, True)
        parsed = urlparse(info['source_url'])
        require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.fragment, '来源地址必须为 HTTPS')
        require(info.get('ribbon_scope', 'COMMON') in {'CARD', 'HERO', 'COMMON'}, '彩带范围无效')
        original_path = path.parent / info['file']
        require(original_path.name == info['file'] and not original_path.is_symlink() and original_path.resolve().is_relative_to(path.parent.resolve()), '原图路径无效')
        original = original_path.read_bytes()
        spec = image_spec(original)
        thumb_path = path.parent / 'thumbnail.webp'
        if build:
            with Image.open(BytesIO(original)) as im:
                thumb = ImageOps.contain(im.convert('RGBA'), (384, 384))
                thumb.save(thumb_path, 'WEBP', quality=86, method=6)
        thumb_data = thumb_path.read_bytes()
        thumb_spec = image_spec(thumb_data, True)
        require(max(thumb_spec['width'], thumb_spec['height']) <= 384, '请重新生成缩略图')
        write_immutable(root / spec['path'], original, build)
        write_immutable(root / thumb_spec['path'], thumb_data, build)
        item = {k: info[k] for k in ['id', 'name', 'category', 'tags', 'author', 'source_url', 'usage']}
        item.update(aliases=info.get('aliases', []), description=info.get('description', ''), ribbon_scope=info.get('ribbon_scope', 'COMMON'),
                    revision=spec['sha256'], original=spec, thumbnail=thumb_spec)
        items.append(item)
    content = {'schema_version': 1, 'tags': tags, 'items': items}
    version = 'resources-' + hashlib.sha256(encoded(content)).hexdigest()[:16]
    catalog = dict(content, version=version)
    data = encoded(catalog)
    require(len(data) <= 8 * 1024 * 1024, '目录超过客户端上限，需要分批维护')
    digest = hashlib.sha256(data).hexdigest()
    manifest_path = f'catalog/manifests/{digest}.json'
    write_immutable(root / manifest_path, data, build)
    index = {'schema_version': 1, 'version': version, 'manifest': manifest_path, 'sha256': digest}
    index_path = root / 'catalog/index.json'
    if build:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_bytes(encoded(index))
    else:
        require(json.loads(index_path.read_text(encoding='utf-8')) == index, '目录未同步，请运行 --build')
    return catalog


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='生成缩略图、不可变文件和目录；默认仅校验')
    args = parser.parse_args()
    result = compile_catalog(build=args.build)
    print(f"OK: {result['version']}, {len(result['items'])} items, {len(result['tags'])} tags")
