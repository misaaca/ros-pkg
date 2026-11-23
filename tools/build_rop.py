#!/usr/bin/env python3
"""
ROS Package Archive (.rop) Builder — byte-exact match for `crates/ros_kernel/src/pkg/rop.rs`.

Usage:
  python3 tools/build_rop.py \
    --name hello-ros \
    --version 1.0.0 \
    --description "Sample ROS utility package" \
    --output packages/hello-ros-1.0.0.rop \
    --file /usr/local/bin/hello-ros:0755:./hello.sh
"""
import argparse
import hashlib
import os
import struct
import sys

ROP_MAGIC = b"ROP\x01"
ROP_VERSION = 1
ROP_HEADER_SIZE = 56


def pack_rop(name: str, version: str, description: str, arch: str, deps: list[str], files: list[tuple[str, int, bytes]]) -> bytes:
    installed_size = sum(len(data) for _, _, data in files)
    deps_toml = ", ".join(f'"{d}"' for d in deps)
    files_toml = ", ".join(f'"{p}"' for p, _, _ in files)
    manifest_toml = (
        f'name = "{name}"\n'
        f'version = "{version}"\n'
        f'description = "{description}"\n'
        f'arch = "{arch}"\n'
        f'installed_size = {installed_size}\n'
        f'dependencies = [{deps_toml}]\n'
        f'files = [{files_toml}]\n'
    ).encode("utf-8")

    payload = bytearray()
    payload.extend(struct.pack("<H", len(files)))
    for vfs_path, mode, data in files:
        pb = vfs_path.encode("utf-8")
        payload.extend(struct.pack("<H", len(pb)))
        payload.extend(pb)
        payload.extend(struct.pack("<I", mode))
        payload.extend(struct.pack("<I", len(data)))
        payload.extend(hashlib.sha256(data).digest())
        payload.extend(data)

    combined = manifest_toml + bytes(payload)
    archive_sha = hashlib.sha256(combined).digest()
    manifest_offset = ROP_HEADER_SIZE
    payload_offset = manifest_offset + len(manifest_toml)

    header = (
        ROP_MAGIC
        + struct.pack("<HHIIII", ROP_VERSION, 0, manifest_offset, len(manifest_toml), payload_offset, len(payload))
        + archive_sha
    )
    assert len(header) == ROP_HEADER_SIZE
    return header + combined


def parse_rop_header_and_manifest(raw: bytes) -> dict:
    if len(raw) < ROP_HEADER_SIZE or raw[:4] != ROP_MAGIC:
        raise ValueError("Invalid .rop magic or truncated header")
    ver, _flags, m_off, m_len, p_off, p_len = struct.unpack("<HHIIII", raw[4:24])
    if ver != ROP_VERSION:
        raise ValueError(f"Unsupported .rop version: {ver}")
    stored_sha = raw[24:56]
    combined = raw[m_off:m_off + m_len] + raw[p_off:p_off + p_len]
    if hashlib.sha256(combined).digest() != stored_sha:
        raise ValueError("ROP internal SHA-256 checksum mismatch")
    manifest_str = raw[m_off:m_off + m_len].decode("utf-8")
    meta = {"name": "", "version": "", "description": "", "arch": "x86_64", "dependencies": []}
    for line in manifest_str.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in ("name", "version", "description", "arch"):
            meta[k] = v.strip('"').strip("'")
        elif k in ("dependencies", "deps"):
            inner = v.strip("[]")
            meta["dependencies"] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip().strip('"').strip("'")]
    return meta


def main():
    ap = argparse.ArgumentParser(description="Build a ROS .rop package archive")
    ap.add_argument("--name", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--description", default="ROS package")
    ap.add_argument("--arch", default="x86_64")
    ap.add_argument("--dep", action="append", default=[])
    ap.add_argument("--file", action="append", required=True, help="VFS_PATH:OCTAL_MODE:LOCAL_FILE")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    file_entries = []
    for spec in args.file:
        vfs_path, mode_oct, local_path = spec.split(":", 2)
        with open(local_path, "rb") as f:
            data = f.read()
        file_entries.append((vfs_path, int(mode_oct, 8), data))

    archive = pack_rop(args.name, args.version, args.description, args.arch, args.dep, file_entries)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "wb") as f:
        f.write(archive)
    print(f"[OK] Built {args.output} ({len(archive)} bytes, SHA256={hashlib.sha256(archive).hexdigest()})")


if __name__ == "__main__":
    main()
