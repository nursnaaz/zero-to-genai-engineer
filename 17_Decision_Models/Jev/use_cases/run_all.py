"""Run every use case end to end and report pass/fail. This is the test suite."""
import subprocess, sys, time, pathlib

folders = sorted(p for p in pathlib.Path(".").iterdir()
                 if p.is_dir() and p.name[0].isdigit())
results = []
for d in folders:
    script = next((s for s in d.glob("*.py")), None)
    if not script:
        results.append((d.name, "NO SCRIPT", 0)); continue
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, script.name], cwd=d,
                       capture_output=True, text=True, timeout=600)
    dt = time.perf_counter() - t0
    status = "PASS" if r.returncode == 0 else "FAIL"
    results.append((d.name, status, dt))
    print(f"{status}  {d.name:<36} {dt:6.1f}s")
    if status == "FAIL":
        print("  " + (r.stderr.strip().splitlines() or ["(no stderr)"])[-1][:200])

print("\n" + "=" * 62)
ok = sum(s == "PASS" for _, s, _ in results)
print(f"{ok}/{len(results)} use cases pass   "
      f"(total wall time {sum(t for _,_,t in results):.0f}s)")
sys.exit(0 if ok == len(results) else 1)
