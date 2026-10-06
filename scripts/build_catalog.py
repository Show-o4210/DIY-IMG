"""Build a bounded Render snapshot from the reviewed source catalog."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from PIL import Image

REPO = "Show-o4210/DIY-IMG"
SCOPES = {"public_git_hosting", "cdn_distribution", "in_app_display", "local_cache", "personal_collection"}
MAX_BYTES = 1048576
IDENTIFIER = re.compile(r"[A-Za-z0-9._-]{1,80}")

def text(value, limit, required=False, multiline=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError("Invalid text field")
    if not multiline and any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Control characters in text")
    return value

def build(root, revision, verify_cdn=False):
    root = Path(root).resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Use a full immutable Git commit SHA")
    source = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    version = source["featured_version"]
    if source.get("schema_version") != 2 or not IDENTIFIER.fullmatch(version):
        raise ValueError("Invalid catalog version")
    entries = source["works"]
    if not isinstance(entries, list) or len(entries) > 50:
        raise ValueError("At most 50 works")
    works, ids = [], set()
    for item in entries:
        work_id = item["id"]
        if not IDENTIFIER.fullmatch(work_id) or work_id in ids:
            raise ValueError("Invalid or duplicated work ID")
        ids.add(work_id)
        authorization = item["authorization"]
        if authorization.get("status") != "approved" or not SCOPES.issubset(set(authorization.get("scopes", []))):
            raise ValueError("Missing approved authorization scopes")
        text(authorization.get("summary"), 2000, required=True, multiline=True)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", authorization.get("confirmed_on", "")):
            raise ValueError("Missing confirmation date")
        path = item["image_path"]
        if not isinstance(path, str) or not path.startswith("works/") or "\\" in path:
            raise ValueError("Use a works/ image path")
        image_path = (root / path).resolve()
        if not image_path.is_relative_to(root / "works") or not image_path.is_file():
            raise ValueError("Image escapes the works directory or is missing")
        if image_path.stat().st_size > MAX_BYTES:
            raise ValueError("Image exceeds 1 MiB")
        raw = image_path.read_bytes()
        with Image.open(image_path) as image:
            width, height = image.size
            if image.format not in {"PNG", "JPEG", "WEBP"} or not 0 < width <= 6000 or not 0 < height <= 6000:
                raise ValueError("Unsupported image")
            output_width = max(640, width)
            if width * height > 12000000 or height * output_width // width > 12000 or height * output_width * output_width // width > 12000000:
                raise ValueError("Image or signed collection dimensions too large")
            image.verify()
        with Image.open(image_path) as image:
            image.load()
        sha = hashlib.sha256(raw).hexdigest()
        url_path = quote(path, safe="/")
        urls = [f"https://{host}/gh/{REPO}@{revision}/{url_path}" for host in
                ["cdn.jsdelivr.net", "fastly.jsdelivr.net", "gcore.jsdelivr.net"]]
        if verify_cdn:
            # Validate a usable primary; fallback hosts are optional and don't block publication.
            with urlopen(Request(urls[0], headers={"User-Agent": "PVZH-DIY-catalog-validator"}), timeout=30) as response:
                cdn = response.read(MAX_BYTES + 1)
            if hashlib.sha256(cdn).hexdigest() != sha:
                raise ValueError("CDN image hash mismatch")
        works.append({"id": work_id, "image_url": urls[0], "image_fallbacks": urls[1:],
                      "source_url": f"https://github.com/{REPO}/blob/{revision}/{url_path}",
                      "sha256": sha, "author_id": text(item["author_id"], 64, required=True),
                      "author_words": text(item.get("author_words", ""), 1000, multiline=True),
                      "license_label": text(item["license_label"], 200, required=True)})
    result = {"schema_version": 2, "featured_version": version, "works": works,
              "source_repository": REPO, "source_revision": revision}
    if len(json.dumps(result, ensure_ascii=False).encode()) > 131072:
        raise ValueError("Manifest exceeds 128 KiB")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-cdn", action="store_true")
    args = parser.parse_args()
    result = build(args.root, args.revision, args.verify_cdn)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
