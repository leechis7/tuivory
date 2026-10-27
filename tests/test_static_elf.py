"""Regression checks for rejecting dynamically linked distribution artifacts."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('static_elf', Path(__file__).resolve().parents[1] / 'tools/check_static_elf.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StaticElfTests(unittest.TestCase):
    def artifact(self, kind, dynamic=b''):
        data = bytearray(120)
        data[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', data, 18, 62)
        struct.pack_into('<Q', data, 32, 64)
        struct.pack_into('<HH', data, 54, 56, 1)
        struct.pack_into('<IIQQQQQQ', data, 64, kind, 0, 120, 0, 0, len(dynamic), 0, 0)
        return data + dynamic

    def check(self, data, arch='x86_64'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'artifact'
            path.write_bytes(data)
            return module.inspect(path, arch)

    def test_static_and_static_pie(self):
        self.assertEqual(self.check(self.artifact(1)), 62)
        self.assertEqual(self.check(self.artifact(2, struct.pack('<qQqQ', 7, 123, 0, 0))), 62)

    def test_interpreter_rejected(self):
        with self.assertRaisesRegex(ValueError, 'interpreter'):
            self.check(self.artifact(3, b'/lib/ld.so\0'))

    def test_needed_without_interpreter_rejected(self):
        with self.assertRaisesRegex(ValueError, 'shared-library'):
            self.check(self.artifact(2, struct.pack('<qQqQ', 1, 42, 0, 0)))

    def test_wrong_architecture_and_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'architecture'):
            self.check(self.artifact(1), 'arm64')
        for data in (b'not ELF', self.artifact(1)[:100]):
            with self.assertRaises(ValueError):
                self.check(data)


if __name__ == '__main__':
    unittest.main()
