#!/usr/bin/env python3
"""Package fetched crates and optional dashboard assets for Gentoo."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(output, directory, names, epoch):
    subprocess.run([
        "tar", "--sort=name", f"--mtime=@{epoch}", "--owner=0", "--group=0",
        "--numeric-owner", "-C", str(directory), "-cJf", str(output), *names,
    ], check=True, env=dict(os.environ, XZ_OPT="-T2 -6"))


def main():
    project, version, commit, source_arg, vendor_arg, output_arg = sys.argv[1:]
    source, vendor, output = map(lambda p: Path(p).resolve(), (source_arg, vendor_arg, output_arg))
    output.mkdir(parents=True, exist_ok=True)
    prefix = f"{project}-{version}"
    manifest_dir = source / "cli" if project == "agent-browser" else source
    manifest = tomllib.loads((manifest_dir / "Cargo.toml").read_text())
    actual_version = manifest.get("package", {}).get("version") or manifest["workspace"]["package"]["version"]
    if actual_version != version:
        raise SystemExit(f"source version {actual_version} does not match {version}")
    epoch = subprocess.check_output(["git", "-C", str(source), "show", "-s", "--format=%ct", commit], text=True).strip()
    crates = []
    for path in sorted((vendor / "cargo_home/gentoo").glob("*/Cargo.toml")):
        package = tomllib.loads(path.read_text())["package"]
        if not (path.parent / ".cargo-checksum.json").is_file():
            raise SystemExit(f"missing cargo checksum: {path.parent.name}")
        crates.append({key: package.get(key) for key in ("name", "version", "license", "license-file", "rust-version")})
    if not crates:
        raise SystemExit("crate bundle is empty")
    archive(output / f"{prefix}-crates.tar.xz", vendor, ["cargo_home"], epoch)
    licenses = {"crates": crates}
    provenance = {
        "project": project, "version": version, "upstream": f"vercel-labs/{project}",
        "tag": f"v{version}", "commit": commit, "source_date_epoch": epoch,
        "cargo_lock_sha256": digest(manifest_dir / "Cargo.lock"),
        "producer_commit": os.environ.get("GITHUB_SHA"),
        "workflow_run": f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
        "cargo": subprocess.check_output(["cargo", "--version"], text=True).strip(),
    }
    if project == "agent-browser":
        dashboard = source / "packages/dashboard"
        page = dashboard / "out/index.html"
        if not page.is_file() or "Dashboard not built" in page.read_text():
            raise SystemExit("dashboard is missing or contains only the placeholder")
        if not any((dashboard / "out/_next").rglob("*.js")):
            raise SystemExit("dashboard has no JavaScript assets")
        notice_dir = dashboard / "web-licenses"
        notice_dir.mkdir(exist_ok=True)
        font_license = source / "Geist-OFL.txt"
        shutil.copyfile(font_license, notice_dir / "Geist-OFL.txt")
        modules = source / "node_modules/.pnpm"
        packages = sorted(set(modules.glob("*/node_modules/*/package.json")) |
                          set(modules.glob("*/node_modules/@*/*/package.json")))
        node_packages = []
        for path in packages:
            package = json.loads(path.read_text())
            name, ver = package.get("name"), package.get("version")
            if not name or not ver:
                continue
            notices = []
            for file in path.parent.iterdir():
                if file.is_file() and file.name.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")):
                    target = notice_dir / f"{name.replace('/', '_')}@{ver}-{file.name}"
                    shutil.copyfile(file, target)
                    notices.append(target.name)
            node_packages.append({"name": name, "version": ver, "license": package.get("license"), "notices": notices})
        licenses["node"] = node_packages
        licenses["fonts"] = [{"name": "Geist", "license": "OFL-1.1", "notice": "Geist-OFL.txt"}]
        provenance.update({
            "pnpm_lock_sha256": digest(source / "pnpm-lock.yaml"),
            "node": subprocess.check_output(["node", "--version"], text=True).strip(),
            "pnpm": subprocess.check_output(["pnpm", "--version"], text=True).strip(),
            "font_license_sha256": digest(font_license),
        })
        archive(output / f"{prefix}-web.tar.xz", dashboard, ["out", "web-licenses"], epoch)
    (output / f"{prefix}-licenses.json").write_text(json.dumps(licenses, indent=2) + "\n")
    (output / f"{prefix}-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    checksum_file = output / f"{prefix}-SHA256SUMS"
    checksum_file.write_text("".join(f"{digest(path)}  {path.name}\n" for path in sorted(output.iterdir()) if path != checksum_file))
    print(f"Packaged {len(crates)} crates for {prefix}")


if __name__ == "__main__":
    main()
