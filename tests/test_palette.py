import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_palette import color_rgb, contrast, inspect


class PaletteChecks(unittest.TestCase):
    def test_known_contrast(self):
        self.assertAlmostEqual(contrast('#000000', '#ffffff'), 21)
        self.assertAlmostEqual(contrast('#008080', '#008080'), 1)

    def test_profile_and_cube(self):
        self.assertEqual(color_rgb('231', 'light-256'), '#ffffff')
        self.assertEqual(color_rgb('16', 'dark-256'), '#000000')
        self.assertEqual(color_rgb('232', 'dark-256'), '#080808')
        with self.assertRaises(ValueError):
            color_rgb('8', 'dark-8')
        with self.assertRaises(ValueError):
            color_rgb('#ffffff', 'dark-16')
        with self.assertRaises(ValueError):
            color_rgb('256', 'dark-256')

    def test_candidate_and_bold_failure(self):
        source = Path(__file__).resolve().parents[1] / 'design/themes/lazyora-candidate.csv'
        count, errors = inspect(source)
        self.assertEqual(count, 192)
        self.assertEqual(errors, [])
        with source.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        # Black-on-olive is readable until ANSI bold maps black to gray.
        row = next(r for r in rows if r['profile'] == 'dark-8' and r['role'] == 'edited')
        row = dict(row, font_weight='bold')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'palette.csv'
            with path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row), lineterminator='\n')
                writer.writeheader()
                writer.writerow(row)
            _, errors = inspect(path)
        self.assertTrue(any('bold-bright contrast' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
