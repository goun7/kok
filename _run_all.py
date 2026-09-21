import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = [
    "f3a_sequencer_proto_en.py",
    "g_layer_tests_en.py",
    "u_layer_prototype_en.py",
    "ghostdag_proto_en.py",
    "fp8_noise_proto_en.py",
    "pass_sim_en.py",
    "bond_margin_proto_en.py",
]

bad = 0
for name in TESTS:
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        print("SKIP  " + name + " (missing)")
        continue
    proc = subprocess.run(
        [sys.executable, path],
        capture_output=True, text=True, timeout=300,
        cwd=HERE,
    )
    status = "rc=" + str(proc.returncode)
    line = ("  " + name + " " * max(1, 30 - len(name)) + status)
    if proc.returncode != 0:
        bad += 1
        line += "  <<< FAIL"
    print(line)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[-400:]
        print("    " + err.replace("\n", "\n    "))

print("\nfailures: " + str(bad))
sys.exit(1 if bad else 0)
