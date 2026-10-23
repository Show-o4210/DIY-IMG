"""Build a public material catalog. Never imports curated works or traverses user libraries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
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


def published_at(info):
    """Missing legacy dates sort before known dates; never infer from local file mtimes."""
    value = info.get('published_at')
    if value is None:
        return 0
    require(isinstance(value, str), '上架时间必须为带时区的 ISO 8601 文字')
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(date.tzinfo is not None, '上架时间必须包含时区')
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        stamp = (date.astimezone(timezone.utc) - epoch) // timedelta(milliseconds=1)
    except (ValueError, OverflowError) as error:
        raise ValueError('上架时间无效') from error
    require(0 <= stamp <= 253402300799999, '上架时间超出范围')
    return stamp


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


def icon_fields(info):
    name = text(info['name'], 80)
    require(len(name.encode('utf-16-le')) // 2 <= 80 and not any(ord(c) < 32 or 127 <= ord(c) <= 159 or c in '\u2028\u2029' for c in name), '图标备注最多 80 个 UTF-16 字符，且须为单行')
    key = info.get('embed_key', '')
    require(isinstance(key, str) and re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', key), '嵌入名须为小写字母开头的 1–64 位字母、数字、横线或下划线')
    # Keep built-in keys in sync with Android IconShortcutCatalog.tokens.
    reserved = {'a', 'amb', 'b', 'd', 'f', 'fast', 'h', 'ha', 'hh', 'hu', 'ice', 'more',
                'nb', 'no', 'noa', 'one', 's', 'st', 't', 'two'}
    require(key not in reserved and not re.fullmatch(r'con|prn|aux|nul|com[1-9]|lpt[1-9]', key), '嵌入名与内置语法或保留文件名冲突')
    return key


def icon_history(root):
    result = []
    for path in (root / 'catalog/manifests').glob('*.json'):
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == path.stem, '历史图标目录校验失败')
        catalog = json.loads(data)
        require(catalog.get('kind') == 'text-icons', '图标目录混入普通素材目录')
        result.extend(catalog['items'])
    return result


def validate_icon_history(info, revision, historical):
    key = icon_fields(info)
    for old in historical:
        require(old['embed_key'] != key or old['id'] == info['id'], '嵌入名已被已发布或已下架图标使用')
        if old['id'] == info['id']:
            require(old['embed_key'] == key and old['revision'] == revision, '已发布图标的嵌入名和图片不可替换；换图请新建条目和嵌入名')


def compile_catalog(root=ROOT, build=False, *, thumbnail_bytes=None, text_icons=False):
    historical = icon_history(root) if text_icons else []
    embed_keys = set()
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
        require((info['category'] == 'TEXT_ICON') == text_icons, '文字图标只能放在 public-assets/text-icons/items；普通素材使用 public-assets/items')
        require(text_icons or 'embed_key' not in info, '带 embed_key 的图标必须使用独立 text-icons 目录')
        if text_icons:
            key = icon_fields(info)
            require(key not in embed_keys, '嵌入名重复')
            embed_keys.add(key)
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
        if text_icons: validate_icon_history(info, spec['sha256'], historical)
        thumb_path = path.parent / 'thumbnail.webp'
        if build:
            if thumbnail_bytes is not None:
                # Optional local-maintainer acceleration; all bytes are still checked below.
                data = thumbnail_bytes[asset_id]
                thumb_path.write_bytes(data.read_bytes() if isinstance(data, Path) else data)
            else:
                with Image.open(BytesIO(original)) as im:
                    thumb = ImageOps.contain(im.convert('RGBA'), (384, 384))
                    thumb.save(thumb_path, 'WEBP', quality=86, method=6)
        thumb_data = thumb_path.read_bytes()
        thumb_spec = image_spec(thumb_data, True)
        require(max(thumb_spec['width'], thumb_spec['height']) <= 384, '请重新生成缩略图')
        write_immutable(root / spec['path'], original, build)
        write_immutable(root / thumb_spec['path'], thumb_data, build)
        item = {k: info[k] for k in ['id', 'name', 'category', 'tags', 'author', 'source_url', 'usage']}
        item.update(aliases=info.get('aliases', []), description=info.get('description', ''), ribbon_scope=info.get('ribbon_scope', 'COMMON'), published_at=published_at(info),
                    revision=spec['sha256'], original=spec, thumbnail=thumb_spec)
        if text_icons: item['embed_key'] = info['embed_key']
        items.append(item)
    content = {'schema_version': 1, 'tags': tags, 'items': items}
    if text_icons: content['kind'] = 'text-icons'
    version = ('text-icons-' if text_icons else 'resources-') + hashlib.sha256(encoded(content)).hexdigest()[:16]
    catalog = dict(content, version=version)
    data = encoded(catalog)
    require(len(data) <= 8 * 1024 * 1024, '目录超过客户端上限，需要分批维护')
    digest = hashlib.sha256(data).hexdigest()
    manifest_path = f'catalog/manifests/{digest}.json'
    write_immutable(root / manifest_path, data, build)
    index = {'schema_version': 1, 'version': version, 'manifest': manifest_path, 'sha256': digest}
    if text_icons: index['kind'] = 'text-icons'
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
    parser.add_argument('--text-icons', action='store_true', help='仅处理 public-assets/text-icons 独立目录')
    args = parser.parse_args()
    result = compile_catalog(ROOT / 'text-icons' if args.text_icons else ROOT, build=args.build, text_icons=args.text_icons)
    print(f"OK: {result['version']}, {len(result['items'])} items, {len(result['tags'])} tags")
