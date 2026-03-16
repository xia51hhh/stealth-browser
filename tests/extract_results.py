"""提取 sannysoft 检测结果文字"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import StealthBrowser


async def extract_results():
    async with StealthBrowser() as browser:
        page = await browser.new_page()

        print("访问 bot.sannysoft.com ...")
        await page.stealth_goto("https://bot.sannysoft.com/")
        await asyncio.sleep(4)

        # 抓取检测结果表格
        results = await page.page.evaluate("""
        () => {
            const rows = document.querySelectorAll('table tr');
            const data = [];
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    const name = cells[0]?.innerText?.trim();
                    const value = cells[1]?.innerText?.trim();
                    const cls = cells[1]?.className || '';
                    const status = cls.includes('failed') ? 'FAIL' :
                                   cls.includes('warn') ? 'WARN' : 'PASS';
                    data.push({name, value: value?.substring(0, 80), status});
                }
            });
            return data;
        }
        """)

        print("\n" + "=" * 70)
        print("  SannySoft Bot Detection 结果")
        print("=" * 70)
        fail_count = 0
        warn_count = 0
        pass_count = 0
        for r in results:
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(r["status"], "?")
            print(f"  {icon} [{r['status']}] {r['name']}: {r['value']}")
            if r["status"] == "FAIL":
                fail_count += 1
            elif r["status"] == "WARN":
                warn_count += 1
            else:
                pass_count += 1

        print(f"\n  汇总: ✅ {pass_count} 通过, ⚠️ {warn_count} 警告, ❌ {fail_count} 失败")
        print("=" * 70)

        # 截个高清图
        await page.page.screenshot(path="screenshots/sannysoft_detail.png",
                                    full_page=True, type="png")

        # 也测试下 navigator.webdriver
        webdriver = await page.page.evaluate("navigator.webdriver")
        print(f"\n  navigator.webdriver = {webdriver}")

        chrome_obj = await page.page.evaluate("!!window.chrome")
        print(f"  window.chrome exists = {chrome_obj}")

        plugins_len = await page.page.evaluate("navigator.plugins.length")
        print(f"  navigator.plugins.length = {plugins_len}")

        permissions = await page.page.evaluate("""
            async () => {
                try {
                    const r = await navigator.permissions.query({name:'notifications'});
                    return r.state;
                } catch(e) { return e.message; }
            }
        """)
        print(f"  permissions.notifications = {permissions}")


if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    asyncio.run(extract_results())
