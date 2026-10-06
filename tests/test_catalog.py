import copy
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from scripts.build_catalog import build, SCOPES

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        image = self.root / "works/sample/image.png"
        image.parent.mkdir(parents=True)
        Image.new("RGB", (640, 960)).save(image)
        self.item = {"id": "sample", "image_path": "works/sample/image.png", "author_id": "测试作者",
                     "author_words": "", "license_label": "仅测试",
                     "authorization": {"status": "approved", "summary": "合成测试数据",
                                       "confirmed_on": "2026-10-06", "scopes": sorted(SCOPES)}}
    def tearDown(self):
        self.temp.cleanup()
    def write(self, works):
        (self.root / "catalog.json").write_text(json.dumps({"schema_version": 2, "featured_version": "test-1", "works": works}), encoding="utf-8")
    def test_empty(self):
        self.write([])
        self.assertEqual([], build(self.root, "a" * 40)["works"])
    def test_pinned_urls_and_hash(self):
        self.write([self.item])
        work = build(self.root, "a" * 40)["works"][0]
        self.assertIn("@" + "a" * 40, work["image_url"])
        self.assertEqual(64, len(work["sha256"]))
    def test_pending_missing_scope_duplicates_and_escape(self):
        for change in [lambda x: x["authorization"].update(status="pending"),
                       lambda x: x["authorization"].update(scopes=[]),
                       lambda x: x.update(image_path="works/../../private.png"),
                       lambda x: x.update(author_id="作者\n伪造")]:
            item = copy.deepcopy(self.item)
            change(item); self.write([item])
            with self.assertRaises(ValueError): build(self.root, "a" * 40)
        self.write([self.item, self.item])
        with self.assertRaises(ValueError): build(self.root, "a" * 40)
    def test_revision_and_image_size(self):
        self.write([self.item])
        with self.assertRaises(ValueError): build(self.root, "main")
        image = self.root / self.item["image_path"]
        image.write_bytes(b"x" * 1048577)
        with self.assertRaises(ValueError): build(self.root, "a" * 40)
