"""
综合检测测试 - 有头模式 (VNC)
访问多个检测网站，提取文字结果并截图
"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import StealthBrowser


async def run():
    os.makedirs("screenshots", exist_ok=True)

    print("=" * 60)
    print("  隐身浏览器 - 综合检测测试")
    print("=" * 60)

    async with StealthBrowser() as browser:
        page = await browser.new_page()

        # === 1. 基础指纹检测 ===
        print("\n[1/4] 检测浏览器基础指纹...")
        await page.page.goto("https://example.com", timeout=30000)
        await asyncio.sleep(1)

        checks = {
            "navigator.webdriver": "navigator.webdriver",
            "window.chrome": "!!window.chrome",
            "chrome.runtime": "!!(window.chrome && window.chrome.runtime)",
            "plugins.length": "navigator.plugins.length",
            "languages": "JSON.stringify(navigator.languages)",
            "platform": "navigator.platform",
            "hardwareConcurrency": "navigator.hardwareConcurrency",
            "deviceMemory": "navigator.deviceMemory",
            "userAgent (前80字)": "navigator.userAgent.substring(0, 80)",
            "maxTouchPoints": "navigator.maxTouchPoints",
            "connection.rtt": "navigator.connection ? navigator.connection.rtt : 'N/A'",
        }
        print("-" * 50)
        all_pass = True
        for label, js in checks.items():
            val = await page.page.evaluate(js)
            # 判断关键项
            if label == "navigator.webdriver" and val is True:
                icon = "FAIL"
                all_pass = False
            elif label == "window.chrome" and not val:
                icon = "FAIL"
                all_pass = False
            elif "HeadlessChrome" in str(val):
                icon = "FAIL"
                all_pass = False
            else:
                icon = "PASS"
            print(f"  [{icon}] {label} = {val}")
        print("-" * 50)

        # === 2. AreYouHeadless 测试 ===
        print("\n[2/4] 访问 arh.antoinevastel.com ...")
        try:
            await page.stealth_goto("https://arh.antoinevastel.com/bots/areyouheadless")
            await asyncio.sleep(3)
            text = await page.page.evaluate("document.body?.innerText || ''")
            is_headless = "headless" in text.lower() and "not" not in text.lower()
            icon = "FAIL" if is_headless else "PASS"
            print(f"  [{icon}] 结果: {text[:100]}")
            fname = f"screenshots/areyouheadless_{int(time.time())}.png"
            await page.page.screenshot(path=fname)
            print(f"  截图: {fname}")
        except Exception as e:
            print(f"  [SKIP] 错误: {e}")

        # === 3. Headless 检测 ===
        print("\n[3/4] 访问 infosimples detect-headless ...")
        try:
            await page.stealth_goto(
                "https://infosimples.github.io/detect-headless/",
                timeout=30000
            )
            await asyncio.sleep(3)

            results = await page.page.evaluate("""
            () => {
                const rows = document.querySelectorAll('table tr');
                const data = [];
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const name = cells[0]?.innerText?.trim();
                        const result = cells[1]?.innerText?.trim();
                        const style = cells[1]?.style?.backgroundColor || '';
                        data.push({name, result, color: style});
                    }
                });
                return data;
            }
            """)
            for r in results:
                is_fail = "red" in r.get("color", "") or "headless" in r.get("result", "").lower()
                icon = "FAIL" if is_fail else "PASS"
                print(f"  [{icon}] {r['name']}: {r['result'][:60]}")

            fname = f"screenshots/detect_headless_{int(time.time())}.png"
            await page.page.screenshot(path=fname, full_page=True)
            print(f"  截图: {fname}")
        except Exception as e:
            print(f"  [SKIP] 错误: {e}")

        # === 4. SannySoft 测试（用 commit 等待策略避免字体卡住） ===
        print("\n[4/4] 访问 bot.sannysoft.com ...")
        try:
            await page.page.goto(
                "https://bot.sannysoft.com/",
                timeout=30000,
                wait_until="commit"
            )
            # 不等 load，等几秒让 JS 跑完就行
            await asyncio.sleep(5)

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
                        data.push({name, value: (value||'').substring(0, 60), status});
                    }
                });
                return data;
            }
            """)

            pass_c = fail_c = warn_c = 0
            for r in results:
                icon = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN"}[r["status"]]
                print(f"  [{icon}] {r['name']}: {r['value']}")
                if r["status"] == "FAIL":
                    fail_c += 1
                elif r["status"] == "WARN":
                    warn_c += 1
                else:
                    pass_c += 1

            print(f"\n  汇总: {pass_c} 通过, {warn_c} 警告, {fail_c} 失败")

            fname = f"screenshots/sannysoft_{int(time.time())}.png"
            await page.page.screenshot(path=fname, full_page=True, timeout=10000)
            print(f"  截图: {fname}")
        except Exception as e:
            print(f"  [SKIP] 错误: {e}")

    print("\n" + "=" * 60)
    print("  测试完成! 截图保存在 screenshots/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run())
