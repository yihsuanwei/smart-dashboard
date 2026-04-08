"""CRM Dashboard UI Test — Playwright automated testing
Tests: page load, filters, tabs, KPI cards, charts, data tables
"""
from playwright.sync_api import sync_playwright
import sys
import os

RESULTS = []
SCREENSHOTS_DIR = "Work/Tools/smart-dashboard/_screenshots"

def log(status, msg):
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    RESULTS.append((status, msg))
    print(f"  {icon} {msg}")

def test_crm_dashboard():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # ── 1. Page Load ──
        print("\n[1/7] Page Load")
        try:
            page.goto("http://localhost:8501/crm_dashboard", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)
            # Wait for Streamlit to finish rendering
            page.wait_for_timeout(3000)
            title_el = page.locator("h1").first
            if title_el.is_visible():
                title_text = title_el.text_content()
                log("PASS", f"Page loaded, title: '{title_text}'")
            else:
                log("FAIL", "Page loaded but no h1 title found")
            page.screenshot(path=f"{SCREENSHOTS_DIR}/01_page_load.png", full_page=True)
        except Exception as e:
            log("FAIL", f"Page load failed: {e}")
            page.screenshot(path=f"{SCREENSHOTS_DIR}/01_page_load_error.png")
            browser.close()
            return

        # ── 2. Check for errors ──
        print("\n[2/7] Error Check")
        error_els = page.locator('[data-testid="stException"]').all()
        if error_els:
            log("FAIL", f"Found {len(error_els)} Streamlit exceptions on page")
            for i, el in enumerate(error_els):
                txt = el.text_content()[:200]
                log("FAIL", f"  Exception {i+1}: {txt}")
        else:
            log("PASS", "No Streamlit exceptions found")

        # Check for st.error messages
        error_msgs = page.locator('[data-testid="stAlert"]').all()
        alert_count = len(error_msgs)
        if alert_count > 0:
            for el in error_msgs:
                txt = el.text_content()[:150]
                log("WARN", f"Alert message: {txt}")
        else:
            log("PASS", "No error/warning alerts")

        # ── 3. KPI Cards ──
        print("\n[3/7] KPI Cards")
        metrics = page.locator('[data-testid="stMetric"]').all()
        if len(metrics) >= 4:
            log("PASS", f"Found {len(metrics)} metric cards (expected ≥4)")
            for m in metrics[:4]:
                label = m.locator('[data-testid="stMetricLabel"]').text_content().strip()
                value = m.locator('[data-testid="stMetricValue"]').text_content().strip()
                log("PASS", f"  KPI: {label} = {value}")
        else:
            log("FAIL", f"Expected ≥4 KPI cards, found {len(metrics)}")

        # ── 4. Filters ──
        print("\n[4/7] Filters")
        # Check tier pills exist
        pills = page.locator('[data-testid="stPills"]').all()
        if pills:
            log("PASS", f"Tier pills filter found")
        else:
            log("WARN", "Tier pills filter not found")

        # Check selectboxes
        selectboxes = page.locator('[data-testid="stSelectbox"]').all()
        log("PASS" if len(selectboxes) >= 2 else "WARN",
            f"Found {len(selectboxes)} selectbox filters")

        # Check search input
        search_inputs = page.locator('[data-testid="stTextInput"]').all()
        log("PASS" if search_inputs else "WARN",
            f"Found {len(search_inputs)} text input(s)")

        # ── 5. Charts (Pie charts) ──
        print("\n[5/7] Charts")
        # Plotly charts render as iframes or divs
        page.wait_for_timeout(2000)  # Give charts time to render
        plotly_charts = page.locator('.stPlotlyChart').all()
        if not plotly_charts:
            plotly_charts = page.locator('[data-testid="stPlotlyChart"]').all()
        if plotly_charts:
            log("PASS", f"Found {len(plotly_charts)} Plotly chart(s)")
        else:
            log("WARN", "No Plotly charts found (may need toggle)")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/02_kpi_and_charts.png", full_page=True)

        # ── 6. Tabs ──
        print("\n[6/7] Tab Navigation")
        tabs = page.locator('[data-baseweb="tab"]').all()
        tab_names = []
        for t in tabs:
            tab_names.append(t.text_content().strip())
        if len(tabs) >= 4:
            log("PASS", f"Found {len(tabs)} tabs: {tab_names}")
        else:
            log("FAIL", f"Expected 4 tabs, found {len(tabs)}: {tab_names}")

        # Test each tab
        for i, tab in enumerate(tabs):
            tab_name = tab_names[i] if i < len(tab_names) else f"Tab {i}"
            try:
                tab.click()
                page.wait_for_timeout(2000)

                # Check for exceptions after tab switch
                exceptions = page.locator('[data-testid="stException"]').all()
                if exceptions:
                    err_text = exceptions[0].text_content()[:200]
                    log("FAIL", f"  Tab '{tab_name}': Exception — {err_text}")
                else:
                    log("PASS", f"  Tab '{tab_name}': Loaded OK")

                page.screenshot(
                    path=f"{SCREENSHOTS_DIR}/03_tab_{i}_{tab_name[:20].replace(' ', '_')}.png",
                    full_page=True
                )
            except Exception as e:
                log("FAIL", f"  Tab '{tab_name}': Click failed — {e}")

        # ── 7. Data Tables ──
        print("\n[7/7] Data Tables")
        dataframes = page.locator('[data-testid="stDataFrame"]').all()
        if dataframes:
            log("PASS", f"Found {len(dataframes)} data table(s) on current tab")
        else:
            log("WARN", "No data tables visible on current tab")

        # Final full-page screenshot
        page.screenshot(path=f"{SCREENSHOTS_DIR}/04_final.png", full_page=True)

        browser.close()

    # ── Summary ──
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    pass_count = sum(1 for s, _ in RESULTS if s == "PASS")
    fail_count = sum(1 for s, _ in RESULTS if s == "FAIL")
    warn_count = sum(1 for s, _ in RESULTS if s == "WARN")
    print(f"  ✅ PASS: {pass_count}")
    print(f"  ❌ FAIL: {fail_count}")
    print(f"  ⚠️  WARN: {warn_count}")
    print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}/")

    if fail_count > 0:
        print("\n❌ FAILURES:")
        for s, msg in RESULTS:
            if s == "FAIL":
                print(f"  - {msg}")

    return fail_count == 0

if __name__ == "__main__":
    success = test_crm_dashboard()
    sys.exit(0 if success else 1)
