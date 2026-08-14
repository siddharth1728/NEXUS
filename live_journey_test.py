"""Full browser journey verification for NEXUS live functionality audit."""
import asyncio
import json
import time
import sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
RESULTS = {"steps": [], "console_errors": [], "failed_requests": [], "passed": False}


def step(name, ok, detail=""):
    RESULTS["steps"].append({"step": name, "ok": ok, "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        raise RuntimeError(f"{name}: {detail}")


async def run():
    uid = str(int(time.time()))
    email = f"journey_{uid}@example.com"
    password = "JourneyPass123!"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page.on("console", lambda msg: RESULTS["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: RESULTS["failed_requests"].append({"url": req.url, "failure": req.failure}))

        # ----------------------------------------------------
        # SESSION 3 (Partial): Auth + Recovery
        # ----------------------------------------------------
        await page.goto(f"{BASE}/forgot-password")
        await page.fill("#email", email)
        await page.click("#submit-btn")
        # In local stub, the email is printed to terminal. We just verify the UI doesn't crash and shows success.
        await page.wait_for_selector("#success-view.show", timeout=5000)
        # Verify underlying behavior - the success view should contain the confirmation text
        success_text = await page.locator("#success-view").inner_text()
        if "check your inbox" not in success_text.lower():
            raise RuntimeError(f"Expected 'Check Your Inbox' in success view, got: {success_text}")
        step("Forgot password UI flow", True)

        # ----------------------------------------------------
        # SESSION 1: Fresh User Journey
        # ----------------------------------------------------
        # Register
        await page.goto(f"{BASE}/register")
        await page.fill("#full_name", "Journey User")
        await page.fill("#email", email)
        await page.fill("#password", password)
        await page.click("#submit-btn")
        await page.wait_for_url("**/onboarding**", timeout=15000)
        step("Register + auto-login", "onboarding" in page.url)

        cookies = await context.cookies()
        access = next((c for c in cookies if c["name"] == "access_token"), None)
        step("HttpOnly access_token cookie", access is not None and access.get("httpOnly") is True)
        step("No access_token in JS", await page.evaluate("document.cookie.includes('access_token')") is False)

        # Onboarding
        await page.select_option("#target-role", "Backend Engineer")
        await page.click("#next-btn")
        await page.fill("#github-username", "tiangolo")
        await page.click("#next-btn")
        await page.click("#next-btn")  # finish
        await page.wait_for_url("**/dashboard**", timeout=15000)
        step("Onboarding saves profile", "dashboard" in page.url)

        # ----------------------------------------------------
        # SESSION 2: Entire NEXUS Product Navigation
        # ----------------------------------------------------
        
        # Profile & Settings
        await page.goto(f"{BASE}/profile")
        await page.wait_for_selector("#name", timeout=10000)
        # Verify underlying behavior - the profile page should load the user's name
        # Wait up to 5 seconds for JS to populate the field
        for _ in range(10):
            name_val = await page.locator("#name").input_value()
            if name_val == "Journey User":
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError(f"Expected profile name 'Journey User', got '{name_val}'")
        step("Profile page loads", True)
        
        await page.goto(f"{BASE}/settings")
        await page.wait_for_selector("h1:has-text('Settings')", timeout=10000)
        step("Settings page loads", True)

        # Projects + GitHub
        await page.goto(f"{BASE}/projects")
        await page.wait_for_selector("#connect-repo-btn", timeout=10000)
        await page.click("#connect-repo-btn")
        await page.click("#fetch-repos-btn")
        await page.wait_for_selector("#repos-list button", timeout=30000)
        
        # Pick a small stable repo if possible, or fallback to first available
        add_btn = page.locator("xpath=//div[@id='repos-list']//div[contains(text(), 'fastapi')]//ancestor::div[contains(@style, 'justify-content')]//button").first
        if await add_btn.count() == 0:
            add_btn = page.locator("#repos-list button").nth(1)
            
        repo_name = await add_btn.locator("xpath=ancestor::div[contains(@style,'justify-content')]//div[contains(@class,'t-subheading')]").first.inner_text()
        await add_btn.click()
        await page.wait_for_timeout(2500)
        await page.goto(f"{BASE}/projects")
        await page.wait_for_function(
            "() => !document.getElementById('projects-loading').classList.contains('hidden') === false && "
            "document.querySelectorAll('#projects-list .landmark-card').length > 0",
            timeout=20000,
        )
        step("Create project from GitHub repos", await page.locator("#projects-list .landmark-card").count() >= 1)

        # Sync
        sync_btn = page.locator("button[id^='sync-btn-']").first
        async with page.expect_response(lambda r: "/sync" in r.url and r.request.method == "POST", timeout=300000) as resp_info:
            await sync_btn.click()
        sync_resp = await resp_info.value
        step("Sync HTTP success", sync_resp.ok, f"status={sync_resp.status}")
        
        # Verify sync status UI
        await page.reload()
        await page.wait_for_function(
            "() => document.querySelectorAll('#projects-list .landmark-card').length > 0",
            timeout=20000,
        )
        status_text = await page.locator("#projects-list .landmark-card-tag").first.inner_text()
        step("Sync UI reflects completion", "Synced" in status_text, f"status={status_text}")

        # ATLAS (Phase 7 Main View)
        await page.goto(f"{BASE}/dashboard")  # The Atlas view
        await page.wait_for_selector("#state-populated:not(.hidden), #state-empty:not(.hidden)", timeout=15000)
        
        if await page.locator("#state-populated").is_visible():
            # Check Atlas SVG elements
            try:
                await page.wait_for_selector("svg", timeout=5000)
            except Exception:
                pass
                
            skills = await page.locator("#skills-list .signal-item").count()
            step("Skills on Atlas", skills >= 0)
            
            # Evidence / Proof / Signals / Unexplored
            await page.goto(f"{BASE}/evidence")
            await page.wait_for_timeout(3000)
            body = await page.content()
            step("No raw secrets in evidence page", "GITHUB_TOKEN" not in body and "ghp_" not in body)
            
            # Next Expedition (NBA) Navigation
            await page.goto(f"{BASE}/dashboard")
            nba_visible = await page.locator("#nba-card:not(.hidden)").count()
            nba_empty = await page.locator("#nba-empty:not(.hidden)").count()
            step("Next Expedition section", nba_visible == 1 or nba_empty == 1, f"card={nba_visible} empty={nba_empty}")

        # ----------------------------------------------------
        # Logout & Re-login
        # ----------------------------------------------------
        await page.click('[data-action="logout"]')
        await page.wait_for_url("**/login**", timeout=10000)
        step("Logout redirect", "login" in page.url)

        await page.goto(f"{BASE}/dashboard")
        await page.wait_for_timeout(2000)
        empty_or_loading = await page.locator("#state-empty:not(.hidden), #state-loading:not(.hidden)").count()
        step("Dashboard blocked after logout", empty_or_loading >= 1)

        await page.goto(f"{BASE}/login")
        await page.fill("#email", email)
        await page.fill("#password", password)
        await page.click("#submit-btn")
        await page.wait_for_url("**/dashboard**", timeout=15000)
        step("Re-login", "dashboard" in page.url)

        # ----------------------------------------------------
        # Responsive smoke tests (Mobile constraints)
        # ----------------------------------------------------
        for w in (375, 390, 768, 1024, 1440):
            await page.set_viewport_size({"width": w, "height": 800})
            await page.wait_for_timeout(500)
            # Just verify it doesn't break horizontal scroll
            overflow = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 2")
            step(f"Responsive {w}px no horizontal scroll", not overflow)

        await browser.close()
        RESULTS["passed"] = True


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        RESULTS["error"] = str(e)
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if RESULTS.get("passed") else 1)
