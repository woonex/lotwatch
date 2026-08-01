import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

URL = "https://www.hyundaimesquite.com/viewdetails/used/jtmab3fv5pd116641/2023-toyota-rav4-prime-sport-utility?type=finance"

async def main():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        print(f"Status: {response.status}")
        html = await page.content()
        print(f"Content length: {len(html)}")
        for term in ["price", "RAV4", "mileage", "application/ld+json", "heated", "403", "cloudflare", "datadome", "jtmab3fv5pd116641"]:
            count = html.lower().count(term.lower())
            if count:
                print(f'  "{term}": {count} occurrences')

asyncio.run(main())
