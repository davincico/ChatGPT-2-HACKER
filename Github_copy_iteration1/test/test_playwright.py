from playwright.sync_api import sync_playwright
#2 modes: async and sync

with sync_playwright() as p:
    # options: chromium, firefox, webkit
    # headless=False to see the browser UI
    # slow_mo=50 to slow down execution
    browser = p.firefox.launch(headless=False, slow_mo=50)
    page = browser.new_page()
    page.goto("https://playwright.dev/")
    print("Title of the webpage is: " + page.title())
    page.screenshot(path="example.png")
    # use this instead of time.sleep(5)
    page.wait_for_timeout(5000)
    browser.close()

####### AYNC ###############

# import asyncio
# from playwright.async_api import async_playwright

# async def main():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False, slow_mo=10)
#         page = await browser.new_page()
#         await page.goto("http://playwright.dev")
#         print(await page.title())
#         await browser.close()

# asyncio.run(main())