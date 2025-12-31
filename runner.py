import subprocess
import sys

try:
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, timeout=10)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
except subprocess.TimeoutExpired as e:
    print("Timeout expired")
    print("Stdout:", e.stdout)
    print("Stderr:", e.stderr)
except Exception as e:
    print(f"Error: {e}")
