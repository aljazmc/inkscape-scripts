"""Tests for scripts/common.py, with Inkscape replaced by a stand-in.
Run: python3 -m unittest discover tests"""
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
common = importlib.import_module("common")


class ExportTest(unittest.TestCase):

    def test_turns_settings_into_inkscape_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "drawing.pdf")

            def inkscape(args, **kwargs):
                output.write_bytes(b"%PDF")  # Inkscape wrote the file
                return mock.Mock(returncode=0, stderr=b"")

            with mock.patch.object(common.subprocess, "run",
                                   side_effect=inkscape) as run:
                common.export("<svg/>", str(output), pdf_version=1.5,
                              text_to_path=True)

        args, kwargs = run.call_args
        self.assertEqual(args[0], [
            "inkscape", "--pipe", "--export-overwrite",
            f"--export-filename={output}",
            "--export-pdf-version=1.5",
            "--export-text-to-path",
        ])
        self.assertEqual(kwargs["input"], b"<svg/>")


if __name__ == "__main__":
    unittest.main()
