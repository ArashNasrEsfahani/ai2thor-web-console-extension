"""Run every offline self-test in sim/ and print one line per suite.

    python scripts/run_selftests.py            # all suites
    python scripts/run_selftests.py step4 trace   # only suites whose name contains one of these words

None of these suites opens the simulator, loads a detector or contacts Ollama, so they run on any machine with
Python 3.10+ (Windows, macOS or Linux), before ai2thor or ultralytics are installed. Each suite runs in its own
process from the repository root (sim/trace.py would shadow the standard-library `trace` module if sim/ were the
working directory).
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    words = sys.argv[1:]
    suites = sorted(glob.glob(os.path.join(ROOT, "sim", "_*_selftest.py")))
    if words:
        suites = [s for s in suites if any(w in os.path.basename(s) for w in words)]
    failed = []
    for path in suites:
        name = os.path.basename(path)[1:-len("_selftest.py")]
        t0 = time.time()
        p = subprocess.run([sys.executable, path], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        lines = [ln for ln in p.stdout.splitlines() if ln.strip(" =-")]
        tail = (lines or [""])[-1].strip()[:90]
        ok = p.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'}  {name:<22} {time.time() - t0:5.1f}s  {tail}")
        if not ok:
            failed.append((name, p.stdout[-2000:] + p.stderr[-2000:]))
    for name, out in failed:
        print(f"\n---- {name} ----\n{out}")
    print(f"\n{len(suites) - len(failed)}/{len(suites)} suites passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
