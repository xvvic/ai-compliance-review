"""Verify the built runtime with a restricted PATH and isolated user data."""
import hashlib
import argparse
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dist/AI-Compliance-Workbench'
VERIFY_ROOT = ROOT / 'build/portable-verification'
BUNDLE = VERIFY_ROOT / '中文 空格目录' / 'AI-Compliance-Workbench'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    if BUNDLE.exists():
        if not BUNDLE.resolve().is_relative_to(VERIFY_ROOT.resolve()):
            raise RuntimeError('Invalid verification directory')
        shutil.rmtree(BUNDLE)
    shutil.copytree(SOURCE, BUNDLE)
    data = VERIFY_ROOT / 'isolated-data'
    data.mkdir(parents=True, exist_ok=True)
    windows = Path(os.environ['SystemRoot'])
    env = {key: value for key, value in os.environ.items() if key.upper() in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'COMSPEC', 'PATHEXT')}
    env.update({'PATH': str(windows / 'System32'), 'COMPLIANCE_DATA_DIR': str(data), 'LOCALAPPDATA': str(VERIFY_ROOT / 'local'), 'APPDATA': str(VERIFY_ROOT / 'roaming'), 'USERPROFILE': str(VERIFY_ROOT / 'profile')})
    python = BUNDLE / 'runtime/python/python.exe'

    def run(*args):
        result = subprocess.run([str(python), *map(str, args)], cwd=BUNDLE, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        if result.returncode:
            raise RuntimeError('Portable subprocess failed: ' + result.stderr[-500:])
        return result.stdout.strip()

    result = json.loads(run('-c', 'import sys,json,server,claude_agent_sdk,psutil,docx,pypdf,yaml; print(json.dumps({"isolated":sys.flags.isolated,"paths":sys.path}))'))
    assert result['isolated'] == 1
    assert all(Path(path).resolve().is_relative_to(BUNDLE.resolve()) for path in result['paths'])
    cli = BUNDLE / 'runtime/python/Lib/site-packages/claude_agent_sdk/_bundled/claude.exe'
    subprocess.run([str(cli), '--version'], cwd=BUNDLE, env=env, capture_output=True, check=True, timeout=30)
    subprocess.run([str(BUNDLE / 'runtime/git/bin/bash.exe'), '--version'], cwd=BUNDLE, env=env, capture_output=True, check=True, timeout=30)
    run('-c', 'from workbench.rag import _index; assert _index()[2] > 0; print("Local BM25 knowledge loaded")')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(url):
        with opener.open(url, timeout=5) as response:
            return response.read()

    blocker = socket.socket()
    try:
        blocker.bind(('127.0.0.1', 8000))
        blocker.listen()
    except OSError:
        pass
    try:
        url = run(BUNDLE / 'launcher.py', 'start', '--no-browser')
        assert url.startswith('http://127.0.0.1:') and not url.endswith(':8000')
        first = json.loads((data / 'instance.json').read_text())
        assert run(BUNDLE / 'launcher.py', 'start', '--no-browser') == url
        second = json.loads((data / 'instance.json').read_text())
        assert first['pid'] == second['pid']
        assert json.loads(get(url + '/api/health'))['status'] == 'ok'
        assert b'<html' in get(url)
        assert json.loads(get(url + '/api/example'))['example'] is True
        assert not json.loads(get(url + '/api/config'))['configured']
        assert get(url + '/report-preview.png').startswith(b'\x89PNG')
        run(BUNDLE / 'launcher.py', 'stop')
        assert not (data / 'instance.json').exists()
        url = run(BUNDLE / 'launcher.py', 'start', '--no-browser')
        assert json.loads(get(url + '/api/health'))['status'] == 'ok'
    finally:
        run(BUNDLE / 'launcher.py', 'stop')
        blocker.close()
    archive = ROOT / 'dist/AI-Compliance-Workbench-Windows-x64.zip'
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        assert not any('/.git/' in name or '/__pycache__/' in name or name.endswith(('.env', '/settings.json', '/instance.json')) for name in names)
        assert not any('/tests/' in name and '/runtime/' not in name for name in names)
        assert not any(name.endswith(('.safetensors', '.gguf', '/pytorch_model.bin')) for name in names)
    digest = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    assert archive.with_suffix('.sha256').read_text().split()[0] == digest
    results = {key: 'passed' for key in ['isolated_imports', 'bundled_cli', 'bundled_bash', 'unicode_space_path', 'port_conflict', 'duplicate_start', 'offline_example', 'preview_asset', 'no_saved_credentials', 'stop_restart', 'package_exclusions', 'sha256']}
    results['environment'] = 'Restricted PATH and isolated profile on existing Windows host; not a fresh Windows VM.'
    results['local_bm25_load'] = 'passed'
    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    (output / 'portable-verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
