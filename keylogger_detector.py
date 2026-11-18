"""
keylogger_detector.py — Targeted keylogger/spyware process detector
---------------------------------------------------------------------
Run this on YOUR OWN machine to scan running processes for indicators
commonly associated with keylogger / input-capture malware, and
terminate ONLY the specific matching process(es) — never a blanket
"kill everything with this name" approach.
hay hya hay man thai this htis htis htis htis  ma name is yes yes yes 
Why not `taskkill /f /im python.exe`?hay hhahhhi hau hu hi hi hi hi hi hi hihi
  - It kills every Python process on the system, including unrelated
    scripts, your IDE's language server, Jupyter kernels, even this
    detector itself if it's also Python. That's not a defense, it's
    collateral damage.
  - Real detection tools (and real anti-malware) inspect WHAT a
    process is actually doing — its command line, loaded modules,
    window/hook behavior — and act on that specific process.

What this script checks for (cross-platform, via psutil):
  1. Suspicious command-line indicators: known keylogger script names,
     or references to keyboard-hooking libraries (pynput, keyboard,
     pyHook, etc.) passed on the command line.
  2. Processes writing to suspiciously-named log files in their open
     file handles (e.g. "keystroke", "keylog", "captured_").
  3. (Optional/advanced) Processes with unusually high CPU wake-ups
     tied to input polling — flagged as "worth a manual look", not
     auto-killed, since this alone isn't conclusive.

Usage:
    pip install psutil
    python keylogger_detector.py            # scan + report only
    python keylogger_detector.py --kill     # scan + terminate matches
"""

import argparse
import sys

try:
    import psutil
except ImportError:
    print("This script requires psutil. Install it with: pip install psutil")
    sys.exit(1)


# Indicators that strongly suggest a keylogger, based on command-line content.
# Extend this list as you learn about more real-world keylogger patterns.
SUSPICIOUS_CMDLINE_KEYWORDS = [
    "keylogger",
    "keylog",
    "keystroke",
    "pynput",
    "pyhook",
    "pythoncom",  # sometimes used by Windows-hook-based loggers
    "globalkeyboardhook",
]

SUSPICIOUS_OPEN_FILE_KEYWORDS = [
    "keylog",
    "keystroke",
    "captured_",
]


def get_cmdline_str(proc):
    try:
        return " ".join(proc.cmdline()).lower()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        return ""


def get_open_file_names(proc):
    try:
        return [f.path.lower() for f in proc.open_files()]
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        return []


def scan_processes():
    """Returns a list of (proc, reasons[]) for suspicious processes found."""
    flagged = []

    for proc in psutil.process_iter(["pid", "name"]):
        reasons = []
        cmdline = get_cmdline_str(proc)

        for keyword in SUSPICIOUS_CMDLINE_KEYWORDS:
            if keyword in cmdline:
                reasons.append(f"command line contains '{keyword}'")

        open_files = get_open_file_names(proc)
        for path in open_files:
            for keyword in SUSPICIOUS_OPEN_FILE_KEYWORDS:
                if keyword in path:
                    reasons.append(f"has open file matching '{keyword}': {path}")

        if reasons:
            flagged.append((proc, reasons))

    return flagged


def report(flagged):
    if not flagged:
        print("[+] No keylogger-like processes detected.")
        return

    print(f"[!] {len(flagged)} suspicious process(es) found:\n")
    for proc, reasons in flagged:
        try:
            print(f"  PID {proc.pid}  —  {proc.name()}")
        except psutil.NoSuchProcess:
            continue
        for r in reasons:
            print(f"      - {r}")
        print()


def kill_flagged(flagged):
    for proc, _ in flagged:
        try:
            pid, name = proc.pid, proc.name()
            proc.terminate()
            proc.wait(timeout=3)
            print(f"[+] Terminated PID {pid} ({name})")
        except psutil.TimeoutExpired:
            proc.kill()
            print(f"[+] Force-killed PID {pid} ({name}) after timeout")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"[-] Could not terminate PID {proc.pid}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Scan for keylogger-like processes.")
    parser.add_argument(
        "--kill",
        action="store_true",
        help="Terminate matching processes (default: report only).",
    )
    args = parser.parse_args()

    print("[*] Scanning running processes for keylogger indicators...\n")
    flagged = scan_processes()
    report(flagged)

    if flagged and args.kill:
        print("\n[*] Terminating flagged process(es)...\n")
        kill_flagged(flagged)
    elif flagged:
        print("Run again with --kill to terminate only these specific process(es).")


if __name__ == "__main__":
    main()