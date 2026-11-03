import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import public_assets
import url_lifecycle

ROOT = Path(__file__).resolve().parents[1]


class ReviewedAliasTests(unittest.TestCase):
    def test_exact_reviewed_repository_identity_target_and_permanent_semantics(self):
        rules = json.loads((ROOT / 'url.lifecycle').read_text()); alias = rules['aliases'][0]
        expected = {'agents.kymatalabs.com': ('ekkolearnai-hermes-studio', 'ekkolearnai-ekko-studio', 1207639951),
                    'voice.kymatalabs.com': ('nvidia-nemo-nemo', 'nvidia-nemo-speech', 200722670)}[rules['host']]
        self.assertEqual(alias['canonical_url'], 'https://' + rules['host'] + '/p/' + expected[0] + '/')
        self.assertEqual(alias['destination'], 'https://' + rules['host'] + '/p/' + expected[1] + '/')
        self.assertEqual(alias['stable_repository_id'], expected[2]); self.assertEqual(alias['status'], 308)
        self.assertIn('proposed', alias['release_state'])
        config = json.loads((ROOT / 'vercel.json').read_text())
        self.assertEqual(len(config['redirects']), 2)
        for route in config['redirects']:
            self.assertIs(route['permanent'], True)  # Documented Vercel semantics:308, preserves method/body.
            self.assertEqual(route['destination'], '/p/' + expected[1] + '/')
            self.assertNotIn(route['destination'].rstrip('/'), [r['source'].rstrip('/') for r in config['redirects']])

    def test_target_is_selfcanonical_in_current_sitemap_and_config_is_uploaded(self):
        rules = json.loads((ROOT / 'url.lifecycle').read_text()); alias = rules['aliases'][0]
        urls = url_lifecycle.urls(ROOT)
        self.assertIn(alias['destination'], urls); self.assertNotIn(alias['canonical_url'], urls)
        self.assertEqual(url_lifecycle.verify(ROOT)['reviewed_proposed_aliases'], 1)
        self.assertIn('vercel.json', public_assets.planned_files(ROOT))

    def test_changed_target_loop_status_or_unreviewed_extra_route_fails(self):
        rules = json.loads((ROOT / 'url.lifecycle').read_text()); original = rules['aliases'][0]
        for mutation in ('loop', 'target', 'status', 'extra', 'noindex', 'googlebot', 'bingbot'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('url.lifecycle', 'vercel.json', 'sitemap.xml'): shutil.copyfile(ROOT / name, root / name)
                target_path = Path(original['destination'].split(rules['host'] + '/')[1]) / 'index.html'
                (root / target_path).parent.mkdir(parents=True); shutil.copyfile(ROOT / target_path, root / target_path)
                changed = copy.deepcopy(rules)
                if mutation == 'loop': changed['aliases'][0]['destination'] = original['canonical_url']
                if mutation == 'target': changed['aliases'][0]['destination'] = 'https://' + rules['host'] + '/p/unreviewed/'
                if mutation == 'status': changed['aliases'][0]['status'] = 307
                if mutation in ('noindex', 'googlebot', 'bingbot'):
                    path = root / target_path
                    name = 'robots' if mutation == 'noindex' else mutation
                    path.write_text(path.read_text().replace('<head>', '<head><meta name="' + name + '" content="noindex,follow">', 1))
                if mutation == 'extra':
                    config = json.loads((root / 'vercel.json').read_text()); config['redirects'].append({'source': '/p/unrelated/', 'destination': '/', 'permanent': True}); (root / 'vercel.json').write_text(json.dumps(config))
                (root / 'url.lifecycle').write_text(json.dumps(changed))
                with self.assertRaises(ValueError): url_lifecycle.verify(root)


if __name__ == '__main__': unittest.main()
