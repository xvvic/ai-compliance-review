"""Build a relocatable Windows distribution from locked dependencies."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = "3.13.12"
PYTHON_SHA256 = "76f238f606250c87c6beac75dccd35ee99070a13490555936abb6cb64ecce3d0"
GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.5/PortableGit-2.55.0.5-64-bit.7z.exe"
GIT_SHA256 = "5aa8a20f6e9abb2c755f0e73c91c687701a46b309ad84a0ca6509380fa4ae290"


def run(*args, cwd=ROOT):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True, creationflags=0x08000000 if os.name == "nt" else 0)


def download(url, destination, expected=None):
    if not destination.exists():
        print("Downloading " + destination.name, flush=True)
        opener = urllib.request.build_opener()
        with opener.open(url, timeout=120) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)
    digest = hashlib.file_digest(destination.open("rb"), "sha256").hexdigest()
    if expected and expected != digest:
        raise RuntimeError("Download checksum mismatch: " + destination.name)
    return digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--proxy", help="Optional build-time HTTP proxy; never included in output")
    args = parser.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if os.name != "nt":
        raise SystemExit("Build this distribution on Windows x64 with Python 3.13.")
    if args.proxy:
        urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({"http": args.proxy, "https": args.proxy})))
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
    cache = ROOT / "build" / "downloads"
    cache.mkdir(parents=True, exist_ok=True)
    bundle = ROOT / "dist" / "AI-Compliance-Workbench"
    if bundle.exists():
        if bundle.resolve().parent != (ROOT / "dist").resolve():
            raise RuntimeError("Invalid output directory")
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    if not args.skip_frontend:
        run("npm.cmd", "ci", cwd=ROOT / "frontend")
        run("npm.cmd", "run", "build", cwd=ROOT / "frontend")
    run(sys.executable, ROOT / "scripts" / "prepare_assets.py")
    for name in ("server.py", "launcher.py", "requirements.lock", "README.md"):
        shutil.copy2(ROOT / name, bundle / name)
    images = bundle / "docs" / "images"
    images.mkdir(parents=True)
    for name in ("workbench.png", "model-settings.png"):
        shutil.copy2(ROOT / "docs" / "images" / name, images / name)
    for name in ("workbench", "assets", "frontend/dist"):
        shutil.copytree(ROOT / name, bundle / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    plugin = Path("claude-code-plugin/ai-startup-compliance-review")
    shutil.copytree(ROOT / plugin, bundle / plugin, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "search[0-9]*.txt", ".env"))
    for source, target in (("start.vbs", "启动应用.vbs"), ("stop.vbs", "停止应用.vbs")):
        shutil.copy2(ROOT / source, bundle / target)
    runtime = bundle / "runtime" / "python"
    python_zip = cache / f"python-{PYTHON_VERSION}-embed-amd64.zip"
    python_hash = download(f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{python_zip.name}", python_zip, PYTHON_SHA256)
    with zipfile.ZipFile(python_zip) as archive:
        archive.extractall(runtime)
    (runtime / "python313._pth").write_text("python313.zip\n.\nLib\\site-packages\nLib\\site-packages\\win32\nLib\\site-packages\\win32\\lib\nLib\\site-packages\\pywin32_system32\n..\\..\n", encoding="ascii")
    pip_args = [sys.executable, "-m", "pip", "install", "--only-binary=:all:", "--no-compile", "--target", str(runtime / "Lib/site-packages"), "-r", str(ROOT / "requirements.lock")]
    if args.proxy:
        pip_args += ["--proxy", args.proxy]
    run(*pip_args)
    # pywin32's system DLLs must be adjacent to python.exe in an embedded runtime.
    for dll in (runtime / "Lib/site-packages/pywin32_system32").glob("*.dll"):
        shutil.copy2(dll, runtime / dll.name)
    git_archive = cache / "PortableGit.7z.exe"
    download(GIT_URL, git_archive, GIT_SHA256)
    run(git_archive, "-y", "-o" + str(bundle / "runtime" / "git"))
    licenses = bundle / "licenses"
    licenses.mkdir()
    (licenses / "runtime-sources.json").write_text(json.dumps({"python": {"version": PYTHON_VERSION, "sha256": python_hash, "url": f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{python_zip.name}"}, "git": {"url": GIT_URL, "sha256": GIT_SHA256}, "python_licenses": "runtime/python/Lib/site-packages/*.dist-info", "git_licenses": "runtime/git/usr/share/licenses"}, indent=2), encoding="utf-8")
    for package in (ROOT / "frontend/node_modules").rglob("package.json"):
        if not any((package.parent / filename).exists() for filename in ("LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.md")):
            continue
        metadata = json.loads(package.read_text(encoding="utf-8"))
        name = metadata.get("name", "").replace("/", "_").replace("@", "")
        if not name:
            continue
        for filename in ("LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.md"):
            source = package.parent / filename
            if source.is_file():
                shutil.copy2(source, licenses / (name + "-" + filename.replace("/", "_")))
    run(runtime / "python.exe", "-c", "import server, claude_agent_sdk, yaml, docx, pypdf, psutil; print('Portable imports OK')", cwd=bundle)
    run(bundle / "runtime/git/bin/bash.exe", "--version", cwd=bundle)
    # The embedded interpreter ignores PYTHONDONTWRITEBYTECODE; remove verification caches.
    for cache_dir in bundle.rglob("__pycache__"):
        if cache_dir.resolve().is_relative_to(bundle.resolve()):
            shutil.rmtree(cache_dir)
    zip_path = Path(shutil.make_archive(str(ROOT / "dist/AI-Compliance-Workbench-Windows-x64"), "zip", ROOT / "dist", bundle.name))
    digest = hashlib.file_digest(zip_path.open("rb"), "sha256").hexdigest()
    zip_path.with_suffix(".sha256").write_text(digest + "  " + zip_path.name + "\n", encoding="ascii")
    print(f"Built {zip_path.name} ({zip_path.stat().st_size / 1024**2:.1f} MB)", flush=True)
    print("SHA256 " + digest)


if __name__ == "__main__":
    main()
