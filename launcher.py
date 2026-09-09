"""Windows portable entry point; never depends on the working directory."""
import argparse
import ctypes
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from workbench.config import DATA_DIR, ROOT, atomic_write
from workbench.jobs import terminate_tree

STATE = DATA_DIR / "instance.json"


def running_instance(check_health=True):
    import psutil
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        process = psutil.Process(state["pid"])
        if abs(process.create_time() - state["created"]) > 0.1 or Path(process.exe()).resolve() != Path(sys.executable).resolve():
            return None
        if "serve" not in process.cmdline():
            return None
        if not check_health:
            return state
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(state["url"] + "/api/health", timeout=1) as response:
            if json.load(response).get("app") == "ai-compliance-workbench":
                return state
    except Exception:
        pass
    return None


def notify(message):
    if os.name == "nt" and not sys.stdout:
        ctypes.windll.user32.MessageBoxW(None, message, "AI Compliance Review", 0x40)
    else:
        print(message)


def serve(port):
    # Closing the job handle (including abrupt process exit) ends all agent children.
    from workbench.windows import contain_process_tree
    handle = contain_process_tree()
    import uvicorn
    from server import app
    runtime = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, log_level="critical"))
    app.state.request_shutdown = lambda: setattr(runtime, "should_exit", True)
    try:
        runtime.run()
    finally:
        if handle:
            ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            ctypes.windll.kernel32.CloseHandle(handle)


def start(open_browser):
    import psutil
    state = running_instance()
    if not state:
        if not (ROOT / "frontend/dist/index.html").exists():
            raise RuntimeError("前端资源缺失，请使用完整便携包；源码开发请先构建前端。")
        with socket.socket() as listener:
            try:
                listener.bind(("127.0.0.1", 8000))
            except OSError:
                listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        process = subprocess.Popen([sys.executable, str(ROOT / "launcher.py"), "serve", "--port", str(port)], cwd=ROOT,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=0x08000000 if os.name == "nt" else 0)
        state = {"pid": process.pid, "created": psutil.Process(process.pid).create_time(), "url": f"http://127.0.0.1:{port}"}
        atomic_write(STATE, json.dumps(state))
        for _ in range(100):
            if running_instance():
                break
            if process.poll() is not None:
                raise RuntimeError("应用服务启动失败，请重新解压完整便携包后重试。")
            time.sleep(0.2)
        else:
            terminate_tree(process.pid)
            raise RuntimeError("应用服务启动超时，请重新启动。")
    if open_browser:
        webbrowser.open(state["url"])
    if sys.stdout:
        print(state["url"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "serve"], nargs="?", default="start")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.action == "serve":
        serve(args.port)
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / "launcher.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            lock.write(b"0")
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        try:
            if args.action == "stop":
                state = running_instance(check_health=False)
                if state:
                    try:
                        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with opener.open(state["url"] + "/api/session", timeout=2) as response:
                            token = json.load(response)["token"]
                        request = urllib.request.Request(state["url"] + "/api/shutdown", data=b"{}", headers={"x-session-token": token, "Content-Type": "application/json"})
                        opener.open(request, timeout=10).close()
                        for _ in range(50):
                            if not running_instance(check_health=False):
                                break
                            time.sleep(0.1)
                    except Exception:
                        pass
                    if running_instance(check_health=False):
                        terminate_tree(state["pid"])
                    STATE.unlink(missing_ok=True)
                notify("应用已停止。")
            else:
                start(not args.no_browser)
        except Exception as exc:
            from workbench.jobs import redact
            message = redact(str(exc))
            atomic_write(DATA_DIR / "logs" / "startup.log", message)
            notify(message)
            raise SystemExit(1)
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
