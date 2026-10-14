# tunnel.py - Multi-Device Access & Dual Persistent Auto-Reconnecting Public Tunnels
import sys
import time
import typing
import threading
import subprocess
import re
import os
import pinggy

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

tunnel_urls = set()

def update_tunnel_file():
    try:
        with open("tunnel_url.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(list(tunnel_urls))))
    except Exception:
        pass

class PersistentPinggyHandler(pinggy.BaseTunnelHandler):
    def tunnel_established(self, url: typing.List[str]):
        print("\n[Pinggy Tunnel] Live Public Link:")
        for u in url:
            print(f"  --> {u}")
            tunnel_urls.add(u)
        update_tunnel_file()
        sys.stdout.flush()

    def disconnected(self, *args, **kwargs):
        print("[Pinggy Tunnel] Reconnecting...")
        sys.stdout.flush()

    def tunnel_failed(self, *args, **kwargs):
        print(f"[Pinggy Tunnel] Failed: {args}")
        sys.stdout.flush()

    def tunnel_error(self, *args, **kwargs):
        print(f"[Pinggy Tunnel] Error: {args}")
        sys.stdout.flush()

    def reconnecting(self, *args, **kwargs):
        pass

    def reconnection_completed(self, *args, **kwargs):
        pass

    def reconnection_failed(self, *args, **kwargs):
        pass

def run_pinggy_thread():
    while True:
        try:
            pinggy.start_tunnel(
                forwardto=8000,
                type="http",
                autoreconnect=True,
                eventclass=PersistentPinggyHandler
            )
        except Exception as e:
            print(f"[Pinggy] Reconnection loop ({e}), retrying in 3s...")
            sys.stdout.flush()
            time.sleep(3)

def run_localhost_run_thread():
    """Persistent localhost.run SSH tunnel (clean direct URL, no interstitial)."""
    while True:
        try:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=3",
                "-R", "80:127.0.0.1:8000",
                "nokey@localhost.run"
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                line_str = line.strip()
                m = re.search(r"https://[a-zA-Z0-9\.\-_]+\.lhr\.life", line_str)
                if m:
                    url = m.group(0)
                    print(f"\n[Direct Tunnel (No Interstitial)]: {url}")
                    tunnel_urls.add(url)
                    update_tunnel_file()
                    sys.stdout.flush()
            proc.wait()
        except Exception as e:
            print(f"[localhost.run] Reconnect notice ({e}), retrying in 3s...")
            sys.stdout.flush()
        time.sleep(3)

def main():
    print("=" * 65)
    print("  RESEARCHMATE AI — DUAL PERSISTENT MULTI-DEVICE LAUNCHER")
    print("  Local Machine:  http://localhost:8000")
    print("  Wi-Fi Network:  http://192.168.1.5:8000 (Open on any phone/tablet/laptop)")
    print("  Starting dual public tunnels: Direct SSH + Pinggy Relay...")
    print("=" * 65)
    sys.stdout.flush()

    t_lhr = threading.Thread(target=run_localhost_run_thread, daemon=False)
    t_lhr.start()

    t_pinggy = threading.Thread(target=run_pinggy_thread, daemon=False)
    t_pinggy.start()

    try:
        t_lhr.join()
    except Exception:
        pass

if __name__ == "__main__":
    main()
