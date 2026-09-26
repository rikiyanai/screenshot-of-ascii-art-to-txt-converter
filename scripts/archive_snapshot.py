"""Read only an immutable, hash-pinned Git snapshot of the private archive.

The archive worktree may contain concurrent or untracked art. No worktree path
is ever used as training or evaluation input.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable, Iterator
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


def load_pair_corpus(archive: Path, path: Path) -> tuple[dict, list[str]]:
    """Load every recursively nested txt/png pair named ``res*``."""
    lock = json.loads(path.read_text(encoding="utf-8"))
    commit = lock["archive_commit"]
    manifest = git_bytes(archive, "show", f"{commit}:MANIFEST.tsv")
    actual_hash = hashlib.sha256(manifest).hexdigest()
    if actual_hash != lock["manifest_sha256"]:
        raise ValueError(f"archive manifest hash mismatch: {actual_hash}")
    declared_hash = git_bytes(archive, "show", f"{commit}:MANIFEST.sha256").split()[0].decode()
    if declared_hash != actual_hash:
        raise ValueError("archive commit's MANIFEST.sha256 disagrees with MANIFEST.tsv")
    files = git_bytes(archive, "ls-tree", "-r", "--name-only", commit, "--", lock["collection"])
    names = files.decode("utf-8").splitlines()
    text = {name[:-4] for name in names if Path(name).name.startswith("res") and name.endswith(".txt")}
    images = {name[:-4] for name in names if Path(name).name.startswith("res") and name.endswith(".png")}
    stems = sorted(text & images)
    if len(stems) != lock["expected_pairs"]:
        raise ValueError(f"expected {lock['expected_pairs']} pairs, found {len(stems)}")
    expected_files = {stem + extension for stem in stems for extension in (".txt", ".png")}
    hashes: dict[str, str] = {}
    encodings: dict[str, str] = {}
    for row in manifest.decode("utf-8").splitlines()[1:]:
        columns = row.split("\t")
        if columns[0] in expected_files:
            hashes[columns[0]] = columns[4]
            encodings[columns[0]] = columns[9]
    if set(hashes) != expected_files:
        raise ValueError("committed pairs and manifest paths disagree")
    font_path = lock.get("font_path")
    if font_path:
        font_rows = [
            row.split("\t") for row in manifest.decode("utf-8").splitlines()[1:]
            if row.split("\t", 1)[0] == font_path
        ]
        if len(font_rows) != 1 or font_rows[0][4] != lock.get("font_sha256"):
            raise ValueError("committed fixed-grid font disagrees with the corpus lock")
        hashes[font_path] = font_rows[0][4]
        encodings[font_path] = font_rows[0][9]
    lock["_file_hashes"] = hashes
    lock["_encodings"] = encodings
    return lock, stems


def read_blob(archive: Path, split: dict, path: str) -> bytes:
    expected = split["_file_hashes"].get(path)
    if expected is None:
        raise ValueError("path is outside the locked pair set")
    body = git_bytes(archive, "show", f"{split['archive_commit']}:{path}")
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError(f"committed blob disagrees with manifest: {path}")
    return body


def read_blobs(archive: Path, split: dict, paths: Iterable[str]) -> Iterator[tuple[str, bytes]]:
    """Stream verified blobs through one ``git cat-file`` process.

    P0C-10: AA-003 has tens of thousands of answer keys. Starting one Git
    process per key made a full prior rebuild needlessly expensive.
    """
    requested = list(paths)
    for path in requested:
        if path not in split["_file_hashes"]:
            raise ValueError(f"path is outside the locked pair set: {path}")
        if "\n" in path or "\r" in path:
            raise ValueError("archive path contains a line break")
    process = subprocess.Popen(
        ["git", "-C", str(archive), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    try:
        for path in requested:
            # P0C-10: request and consume one object at a time. Writing tens of
            # thousands of requests up front deadlocks when cat-file blocks on
            # its full stdout pipe while the parent is still filling stdin.
            process.stdin.write(f"{split['archive_commit']}:{path}\n".encode())
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii").rstrip("\n")
            fields = header.split()
            if len(fields) != 3 or fields[1] != "blob":
                raise ValueError(f"cannot read committed blob {path}: {header}")
            size = int(fields[2])
            body = process.stdout.read(size)
            if len(body) != size or process.stdout.read(1) != b"\n":
                raise ValueError(f"truncated Git blob stream: {path}")
            if hashlib.sha256(body).hexdigest() != split["_file_hashes"][path]:
                raise ValueError(f"committed blob disagrees with manifest: {path}")
            yield path, body
        process.stdin.close()
        if process.wait() != 0:
            error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            raise subprocess.CalledProcessError(process.returncode, process.args, stderr=error)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
