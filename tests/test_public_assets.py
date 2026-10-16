import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

MODULE = Path(__file__).resolve().parents[1] / 'scripts/build_public_assets.py'
spec = importlib.util.spec_from_file_location('public_assets', MODULE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PublicAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'items/subject-test').mkdir(parents=True)
        (self.root / 'tags.json').write_text(json.dumps([{'id': 'flower', 'label': '花朵', 'aliases': ['花卉']}]), encoding='utf-8')
        self.info = {'id': 'subject-test', 'name': '测试花朵', 'category': 'SUBJECT', 'tags': ['flower'],
                     'author': '测试', 'source_url': 'https://example.org/source', 'usage': '仅测试', 'file': 'original.png'}
        self.write_info()
        Image.new('RGBA', (64, 80), 'yellow').save(self.root / 'items/subject-test/original.png')

    def tearDown(self):
        self.temp.cleanup()

    def write_info(self):
        (self.root / 'items/subject-test/info.json').write_text(json.dumps(self.info), encoding='utf-8')

    def test_generated_catalog_passes_check_and_detects_modified_blob(self):
        catalog = builder.compile_catalog(self.root, True)
        self.assertEqual(catalog, builder.compile_catalog(self.root))
        blob = self.root / catalog['items'][0]['original']['path']
        blob.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            builder.compile_catalog(self.root)

    def test_unknown_tag_and_directory_traversal_are_rejected(self):
        self.info['tags'] = ['missing']; self.write_info()
        with self.assertRaises(ValueError):
            builder.compile_catalog(self.root, True)
        self.info['tags'] = ['flower']; self.info['file'] = '../original.png'; self.write_info()
        with self.assertRaises(ValueError):
            builder.compile_catalog(self.root, True)

    def test_new_original_keeps_old_published_files(self):
        old = builder.compile_catalog(self.root, True)
        old_item = old['items'][0]
        Image.new('RGBA', (64, 80), 'pink').save(self.root / 'items/subject-test/original.png')
        new = builder.compile_catalog(self.root, True)
        self.assertEqual(old_item['id'], new['items'][0]['id'])
        self.assertNotEqual(old_item['revision'], new['items'][0]['revision'])
        self.assertTrue((self.root / old_item['original']['path']).exists())
        self.assertEqual(2, len(list((self.root / 'catalog/manifests').glob('*.json'))))

    def test_metadata_update_changes_catalog_but_not_image_revision(self):
        old = builder.compile_catalog(self.root, True)
        self.info['name'] = '新的显示名称'; self.write_info()
        new = builder.compile_catalog(self.root, True)
        self.assertNotEqual(old['version'], new['version'])
        self.assertEqual(old['items'][0]['revision'], new['items'][0]['revision'])

    def test_publication_time_is_explicit_timezone_aware_and_legacy_optional(self):
        old = builder.compile_catalog(self.root, True)
        self.assertEqual(0, old['items'][0]['published_at'])
        self.info['published_at'] = '2024-01-01T08:00:00+08:00'; self.write_info()
        new = builder.compile_catalog(self.root, True)
        self.assertEqual(1704067200000, new['items'][0]['published_at'])
        self.assertEqual(old['items'][0]['revision'], new['items'][0]['revision'])
        for bad in ['2024-01-01', 'not-a-date', '1969-01-01T00:00:00Z', 1704067200000]:
            self.info['published_at'] = bad; self.write_info()
            with self.assertRaises(ValueError):
                builder.compile_catalog(self.root, True)


if __name__ == '__main__':
    unittest.main()
