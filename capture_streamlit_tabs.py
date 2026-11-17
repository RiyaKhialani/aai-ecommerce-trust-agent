"""
Captures high-resolution screenshots of each tab in the Streamlit application using Microsoft Edge.
"""

import time
import subprocess
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def main():
    print("Launching Streamlit...")
    proc = subprocess.Popen(
        ['python', '-m', 'streamlit', 'run', 'streamlit_app.py', '--server.port=8540', '--server.headless=true', '--browser.gatherUsageStats=false'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(4.5)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1600,1050')
    options.add_argument('--disable-gpu')

    try:
        driver = webdriver.Edge(options=options)
        driver.get('http://127.0.0.1:8540')
        time.sleep(5.0)  # Wait for full React render

        # 1. Main Dashboard Overview
        driver.save_screenshot('screenshot_streamlit_dashboard.png')
        print("Captured screenshot_streamlit_dashboard.png")

        # Function to click a tab by text
        def click_tab(tab_name):
            try:
                # Find any element containing tab_name in its full text string
                elems = driver.find_elements(By.XPATH, f"//*[contains(., '{tab_name}') and (self::p or self::button)]")
                if not elems:
                    print(f"No element found for '{tab_name}'")
                    return False
                # Pick the smallest element (deepest in tree)
                target = elems[-1]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                driver.execute_script("arguments[0].click();", target)
                time.sleep(2.0)
                print(f"Successfully clicked '{tab_name}'")
                return True
            except Exception as e:
                print(f"Error clicking '{tab_name}': {e}")
                return False

        # 2. Tab 1: 10-Agent Pipeline Trace
        if click_tab("10-Agent"):
            driver.save_screenshot('screenshot_streamlit_pipeline.png')
            print("Captured screenshot_streamlit_pipeline.png")

        # 3. Tab 2: Itemized Evidentiary Dossier
        if click_tab("Evidentiary"):
            driver.save_screenshot('screenshot_streamlit_evidence.png')
            print("Captured screenshot_streamlit_evidence.png")

        # 4. Tab 3: Review Velocity & Bursts (with Plotly Chart)
        if click_tab("Velocity"):
            time.sleep(1.0)
            driver.save_screenshot('screenshot_streamlit_cohorts.png')
            print("Captured screenshot_streamlit_cohorts.png")

        # 5. Tab 4: Contract Claim Redlines
        if click_tab("Redlines"):
            driver.save_screenshot('screenshot_streamlit_redlines.png')
            print("Captured screenshot_streamlit_redlines.png")

        # 6. Tab 5: Trust Agent Chat & RAG
        if click_tab("Chat & RAG") or click_tab("Trust Agent Chat"):
            time.sleep(1.5)
            driver.save_screenshot('screenshot_streamlit_chat_rag.png')
            print("Captured screenshot_streamlit_chat_rag.png")

        # 7. Tab 6: LLM Inference Optimization
        if click_tab("Optimization") or click_tab("LLM Inference"):
            time.sleep(1.5)
            driver.save_screenshot('screenshot_streamlit_optimization.png')
            print("Captured screenshot_streamlit_optimization.png")

        # 8. Tab 7: Safety Guardrails & PII
        if click_tab("Safety Guardrails") or click_tab("Guardrails"):
            time.sleep(1.5)
            driver.save_screenshot('screenshot_streamlit_guardrails.png')
            print("Captured screenshot_streamlit_guardrails.png")

        # 9. Tab 8: Audit History & Data
        if click_tab("Audit History") or click_tab("History & Data"):
            time.sleep(1.5)
            driver.save_screenshot('screenshot_streamlit_history.png')
            print("Captured screenshot_streamlit_history.png")

        # 10. Tab 10: Verbose Audit Logs (Gemini 3.8)
        if click_tab("Verbose Audit") or click_tab("Audit Logs") or click_tab("Gemini 3.8"):
            time.sleep(1.0)
            # Find and expand the first two expanders
            expanders = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stExpander'] summary")
            print(f"Found {len(expanders)} expanders in Audit Logs tab")
            if expanders:
                driver.execute_script("arguments[0].click();", expanders[0])
                time.sleep(1.0)
            if len(expanders) > 1:
                driver.execute_script("arguments[0].click();", expanders[1])
                time.sleep(1.0)
            driver.save_screenshot('screenshot_streamlit_audit_logs.png')
            print("Captured screenshot_streamlit_audit_logs.png")

        driver.quit()
        print("\nAll Streamlit tabs captured successfully via Microsoft Edge!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    main()
