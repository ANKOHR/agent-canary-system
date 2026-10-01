"""Launcher for the Agent Canary System build. Spawns codex.exe detached with a
console so it survives SSH teardown. Launched via WMI Win32_Process.Create."""
import os
import subprocess
import time

BASE = r"C:\Users\henry\Documents\agent-canary-system"
CODEX = r"C:\Users\henry\.codex\plugins\.plugin-appserver\codex.exe"
PROMPT_FILE = os.path.join(BASE, "agent-canary-system-prompt.txt")
LOG_FILE = os.path.join(BASE, "agent-canary-system-codex.log")

os.makedirs(BASE, exist_ok=True)

with open(PROMPT_FILE, encoding="utf-8") as f:
    prompt = f.read()

logf = open(LOG_FILE, "ab")
logf.write(("=== agent-canary-system launch %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S")).encode("utf-8"))
logf.flush()

proc = subprocess.Popen(
    [CODEX, "exec", "--skip-git-repo-check"],
    stdin=subprocess.PIPE,
    stdout=logf,
    stderr=subprocess.STDOUT,
    cwd=BASE,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)
proc.communicate(prompt.encode("utf-8"))
logf.write(("=== codex exited %d at %s ===\n" % (proc.returncode, time.strftime("%Y-%m-%d %H:%M:%S"))).encode("utf-8"))
logf.close()
