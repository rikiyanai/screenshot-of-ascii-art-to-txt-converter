"""The corpus split reads committed Git blobs, never the mutable worktree."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archive_snapshot import load_split, read_blob  # noqa: E402


class LockedArchive(unittest.TestCase):
    def test_uses_only_pinned_pairs_and_checks_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "archive"
            root.mkdir()

            def git(*args: str) -> str:
                return subprocess.run(["git", "-C", str(root), *args], check=True,
                                      capture_output=True, text=True).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            files = {}
            for slug, stem in (("one", "res1"), ("two", "resK-01")):
                for extension, body in (("txt", b"a\n"), ("png", b"fake image")):
                    name = f"collections/aahub/{slug}/{stem}.{extension}"
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(body)
                    files[name] = hashlib.sha256(body).hexdigest()
            manifest = "path\tcategory\tdesc\tupstream\tsha256\tbytes\tlicense\tredistribute\tprovenance\tencoding\tpair\n"
            manifest += "".join(f"{name}\tx\tx\tx\t{digest}\t1\tx\tx\tx\tx\tx\n"
                                for name, digest in sorted(files.items()))
            digest = hashlib.sha256(manifest.encode()).hexdigest()
            (root / "MANIFEST.tsv").write_text(manifest, encoding="utf-8")
            (root / "MANIFEST.sha256").write_text(f"{digest}  MANIFEST.tsv\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "fixture")
            commit = git("rev-parse", "HEAD")
            split_path = Path(temporary) / "split.json"
            split_path.write_text(json.dumps({
                "archive_commit": commit, "manifest_sha256": digest,
                "collection": "collections/aahub", "expected_slugs": 2,
                "expected_pairs": 2, "held_out_slugs": ["two"],
            }), encoding="utf-8")

            # Concurrent worktree changes must not affect the locked snapshot.
            (root / "collections/aahub/one/res1.txt").write_text("changed\n", encoding="utf-8")
            extra = root / "collections/aahub/new/res2.txt"
            extra.parent.mkdir(parents=True)
            extra.write_text("untracked\n", encoding="utf-8")
            split, jobs = load_split(root, split_path)
            self.assertEqual(sum(map(len, jobs.values())), 2)
            self.assertEqual(read_blob(root, split, jobs["one"][0] + ".txt"), b"a\n")
            with self.assertRaises(ValueError):
                read_blob(root, split, "collections/aahub/new/res2.txt")


if __name__ == "__main__":
    unittest.main()
