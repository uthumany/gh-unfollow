import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_python_requires_310(self):
        metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.10"', metadata)
        self.assertNotIn('"Programming Language :: Python :: 3.8"', metadata)
        self.assertNotIn('"Programming Language :: Python :: 3.9"', metadata)

    def test_npm_bin_uses_cross_platform_launcher(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["bin"]["gh-unfollow"], "bin/gh-unfollow.js")
        self.assertEqual(package["bin"]["github-unfollow"], "bin/gh-unfollow.js")

    def test_npm_pack_excludes_bytecode_and_launcher_smoke(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)
            packed = subprocess.run(
                ["npm", "pack", "--pack-destination", str(destination)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            archive = next(destination.glob("*.tgz"))
            with tarfile.open(archive) as tar:
                names = tar.getnames()
                self.assertIn("package/bin/gh-unfollow.js", names)
                self.assertNotIn("package/src/__pycache__/main.cpython-312.pyc", names)

            install = destination / "install"
            subprocess.run(
                ["npm", "install", "--prefix", str(install), str(archive), "--ignore-scripts"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [str(install / "node_modules/.bin/gh-unfollow"), "--help"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
