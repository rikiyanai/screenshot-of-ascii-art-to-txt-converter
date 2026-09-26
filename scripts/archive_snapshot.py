"""Read only an immutable, hash-pinned Git snapshot of the private archive.

The archive worktree may contain concurrent or untracked art. No worktree path
is ever used as training or evaluation input.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

SPLIT = Path(__file__).resolve().parent.parent / "data/aahub_split.json"


def git_bytes(archive: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(archive), *args], check=True, capture_output=True
    ).stdout


def load_split(archive: Path, path: Path = SPLIT) -> tuple[dict, dict[str, list[str]]]:
    split = json.loads(path.read_text(encoding="utf-8"))
    commit = split["archive_commit"]
    manifest = git_bytes(archive, "show", f"{commit}:MANIFEST.tsv")
    actual_hash = hashlib.sha256(manifest).hexdigest()
    if actual_hash != split["manifest_sha256"]:
        raise ValueError(f"archive manifest hash mismatch: {actual_hash}")
    declared_hash = git_bytes(archive, "show", f"{commit}:MANIFEST.sha256").split()[0].decode()
    if declared_hash != actual_hash:
        raise ValueError("archive commit's MANIFEST.sha256 disagrees with MANIFEST.tsv")
    prefix = split["collection"] + "/"
    paths = git_bytes(archive, "ls-tree", "-r", "--name-only", commit, "--", split["collection"])
    files = paths.decode("utf-8").splitlines()
    pairs: dict[str, dict[str, set[str]]] = {}
    for name in files:
        if not name.startswith(prefix):
            continue
        rest = name[len(prefix):]
        parts = rest.split("/")
        if len(parts) != 2 or not parts[1].startswith("res"):
            continue
        slug, filename = parts
        stem, dot, extension = filename.rpartition(".")
        if dot and extension in ("txt", "png"):
            pairs.setdefault(slug, {"txt": set(), "png": set()})[extension].add(stem)
    slugs = sorted({name[len(prefix):].split("/", 1)[0] for name in files
                    if name.startswith(prefix) and "/" in name[len(prefix):]})
    if len(slugs) != split["expected_slugs"]:
        raise ValueError(f"expected {split['expected_slugs']} slugs, found {len(slugs)}")
    if set(split["held_out_slugs"]) - set(slugs):
        raise ValueError("held-out split names a slug absent from the committed archive")
    if any(p["txt"] != p["png"] for p in pairs.values()):
        raise ValueError("committed AAHub text/image pairs do not match")
    total = sum(len(p["txt"]) for p in pairs.values())
    if total != split["expected_pairs"]:
        raise ValueError(f"expected {split['expected_pairs']} pairs, found {total}")
    jobs = {
        slug: [f"{prefix}{slug}/{stem}" for stem in sorted(pairs.get(slug, {}).get("txt", ()))]
        for slug in slugs
    }
    expected_files = {stem + ext for stems in jobs.values() for stem in stems for ext in (".txt", ".png")}
    hashes = {}
    for row in manifest.decode("utf-8").splitlines()[1:]:
        columns = row.split("\t")
        if columns[0] in expected_files:
            hashes[columns[0]] = columns[4]
    if set(hashes) != expected_files:
        raise ValueError("committed pairs and manifest paths disagree")
    split["_file_hashes"] = hashes
    return split, jobs


def read_blob(archive: Path, split: dict, path: str) -> bytes:
    expected = split["_file_hashes"].get(path)
    if expected is None:
        raise ValueError("path is outside the locked pair set")
    body = git_bytes(archive, "show", f"{split['archive_commit']}:{path}")
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError(f"committed blob disagrees with manifest: {path}")
    return body
