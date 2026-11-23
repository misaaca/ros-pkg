#!/usr/bin/env python3
"""
Verifies integrity of the ROS Package Repository (Packages.toml, kernel binary, and .rop archives).
Called automatically by `ROS/scripts/publish_to_repo.sh`.
"""
import hashlib
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from build_rop import parse_rop_header_and_manifest


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    pjson = os.path.join(REPO_ROOT, "Packages.json")
    ptoml = os.path.join(REPO_ROOT, "Packages.toml")
    if not os.path.isfile(pjson) or not os.path.isfile(ptoml):
        print("[FAIL] Missing Packages.toml or Packages.json — run python3 tools/update_index.py")
        sys.exit(1)

    data = json.load(open(pjson, encoding="utf-8"))
    k = data.get("kernel")
    if k:
        kpath = os.path.join(REPO_ROOT, k["filename"])
        if not os.path.isfile(kpath):
            print(f"[FAIL] Missing kernel binary: {k['filename']}")
            sys.exit(1)
        actual = sha256_file(kpath)
        if actual != k["sha256"]:
            print(f"[FAIL] Kernel SHA256 mismatch: expected {k['sha256']}, got {actual}")
            sys.exit(1)
        print(f"[PASS] kernel: {k['filename']} (v{k['version']}+{k['build']}, SHA256 OK)")

    for p in data.get("packages", []):
        ppath = os.path.join(REPO_ROOT, p["filename"])
        if not os.path.isfile(ppath):
            print(f"[FAIL] Missing package: {p['filename']}")
            sys.exit(1)
        raw = open(ppath, "rb").read()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != p["sha256"]:
            print(f"[FAIL] Package SHA256 mismatch for {p['name']}")
            sys.exit(1)
        parse_rop_header_and_manifest(raw)
        print(f"[PASS] package: {p['name']} v{p['version']} ({p['filename']}, ROP+SHA256 OK)")

    print("[OK] Repository verification passed.")


if __name__ == "__main__":
    main()
