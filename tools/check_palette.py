#!/usr/bin/env python3
"""Validate draft palette CSV files using a documented reference palette."""
import argparse
import csv
import math
import re
import sys
from pathlib import Path

ANSI = ('#000000', '#800000', '#008000', '#808000', '#000080', '#800080',
        '#008080', '#c0c0c0', '#808080', '#ff0000', '#00ff00', '#ffff00',
        '#0000ff', '#ff00ff', '#00ffff', '#ffffff')
REQUIRED = {'profile', 'role', 'foreground', 'background', 'reference_fg',
            'reference_bg', 'contrast', 'target', 'font_weight'}


def color_rgb(value, profile):
    count = profile.rsplit('-', 1)[-1]
    if count not in ('8', '16', '256', 'truecolor'):
        raise ValueError('unknown color profile: ' + profile)
    if re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        if count != 'truecolor':
            raise ValueError('RGB requires a truecolor profile')
        return value.lower()
    if not re.fullmatch(r'\d+', value):
        raise ValueError('expected a color index or #RRGGBB: ' + value)
    index = int(value)
    limit = 256 if count == 'truecolor' else int(count)
    if not 0 <= index < limit:
        raise ValueError('color index outside profile: ' + value)
    if index < 16:
        return ANSI[index]
    if index >= 232:
        return '#{0:02x}{0:02x}{0:02x}'.format(8 + (index - 232) * 10)
    n = index - 16
    levels = (0, 95, 135, 175, 215, 255)
    return '#{:02x}{:02x}{:02x}'.format(levels[n // 36], levels[n // 6 % 6], levels[n % 6])


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(fg, bg):
    low, high = sorted((luminance(fg), luminance(bg)))
    return (high + .05) / (low + .05)


def inspect(path):
    errors, seen = [], set()
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED.issubset(reader.fieldnames or []):
            return 0, ['missing required CSV columns']
        for line, row in enumerate(reader, 2):
            try:
                key = (row['profile'], row['role'])
                if not all(key) or key in seen:
                    raise ValueError('empty or duplicate profile/role')
                seen.add(key)
                fg = color_rgb(row['foreground'], row['profile'])
                bg = color_rgb(row['background'], row['profile'])
                if (fg, bg) != (row['reference_fg'].lower(), row['reference_bg'].lower()):
                    raise ValueError('reference RGB does not match color values')
                target, reported = float(row['target']), float(row['contrast'])
                if not all(math.isfinite(v) and 1 <= v <= 21 for v in (target, reported)):
                    raise ValueError('target/contrast must be finite and between 1 and 21')
                normal = contrast(fg, bg)
                if abs(normal - reported) > .01:
                    raise ValueError('reported contrast differs from computed value')
                if normal < target:
                    raise ValueError('normal contrast {:.3f} < {:.3f}'.format(normal, target))
                if row['font_weight'] not in ('none', 'bold'):
                    raise ValueError('font_weight must be none or bold')
                if row['font_weight'] == 'bold' and row['foreground'].isdigit() and int(row['foreground']) < 8:
                    bright = contrast(ANSI[int(row['foreground']) + 8], bg)
                    if bright < target:
                        raise ValueError('bold-bright contrast {:.3f} < {:.3f}'.format(bright, target))
            except (ValueError, TypeError, AttributeError) as error:
                errors.append('line {}: {}'.format(line, error))
    if not seen:
        errors.append('no palette rows')
    return len(seen), errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    try:
        count, errors = inspect(args.csv)
    except (OSError, UnicodeError, csv.Error) as error:
        print(error, file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('{} palette pairs passed reference checks; actual terminals require separate evidence.'.format(count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
