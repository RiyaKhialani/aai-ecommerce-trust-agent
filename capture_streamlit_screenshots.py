"""
Captures high-resolution Microsoft Edge screenshots of the Streamlit application.
"""

import subprocess
import time
import os
import sys
import requests

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

PORT = 8501
URL = f"http://127.0.0.1:{PORT}"


def wait_for_streamlit(url, max_attempts=25):
    for i in range(max_attempts):
        try:
            r = requests.get(f"{url}/_stcore/health", timeout=1)
            if r.status_code == 200:
                print(f"Streamlit server is ready on attempt {i+1}!")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def capture_screenshot(url, output_path, window_size="1360,940", delay_ms=4000):
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--window-size={window_size}",
        f"--virtual-time-budget={delay_ms}",
        f"--screenshot={output_path}",
        url
    ]
    subprocess.run(cmd, capture_output=True, timeout=25)
    print(f"Captured {os.path.basename(output_path)} -> {os.path.exists(output_path)} ({os.path.getsize(output_path) if os.path.exists(output_path) else 0} bytes)")


def main():
    print(f"Launching Streamlit on port {PORT}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    st_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "streamlit_app.py",
            f"--server.port={PORT}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        ready = wait_for_streamlit(URL)
        if not ready:
            print("Failed to connect to Streamlit server!")
            return

        time.sleep(2)  # Allow initial Streamlit script execution

        # Capture Screenshot 1: Streamlit Main Dashboard & KPI Metrics
        capture_screenshot(
            URL,
            os.path.abspath("screenshot_streamlit_dashboard.png"),
            window_size="1360,960",
            delay_ms=4500
        )

        # Capture Screenshot 2: Pipeline Stepper & Evidentiary Table
        capture_screenshot(
            URL,
            os.path.abspath("screenshot_streamlit_pipeline.png"),
            window_size="1360,1050",
            delay_ms=4500
        )

        print("\nAll Streamlit screenshots captured successfully via Microsoft Edge!")

    finally:
        st_proc.terminate()
        try:
            st_proc.wait(timeout=3)
        except Exception:
            st_proc.kill()


if __name__ == "__main__":
    main()
