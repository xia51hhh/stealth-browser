"""
反检测效果测试 - 访问多个bot检测站点，提取关键检测项结果
"""
import asyncio
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from camoufox.async_api import AsyncCamoufox

TESTS = [
    {
        "name": "sannysoft",
        "url": "https://bot.sannysoft.com",
        "extract": """
            () => {
                const rows = document.querySelectorAll('table tr');
                const results = {};
                rows.forEach(r => {
                    const cells = r.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const key = cells[0].innerText.trim();
                        const val = cells[1].innerText.trim();
                        const cls = cells[1].className || '';
                        results[key] = {value: val, status: cls.includes('passed') ? 'PASS' : cls.includes('failed') ? 'FAIL' : val};
                    }
                });
                return results;
            }
        """
    },
    {
        "name": "creepjs",
        "url": "https://abrahamjuliot.github.io/creepjs/",
        "extract": """
            () => {
                // 等creepjs渲染完毕后提取信任分数
                const el = document.querySelector('#fingerprint-data') ||
                           document.querySelector('.visitor-info') ||
                           document.querySelector('[class*="trust"]');
                return {
                    title: document.title,
                    bodyText: document.body.innerText.slice(0, 500)
                };
            }
        """
    },
    {
        "name": "browserleaks_js",
        "url": "https://browserleaks.com/javascript",
        "extract": """
            () => {
                const rows = document.querySelectorAll('tr');
                const results = {};
                rows.forEach(r => {
                    const cells = r.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const key = cells[0].innerText.trim();
                        const val = cells[1].innerText.trim();
                        if (key && val) results[key] = val;
                    }
                });
                return results;
            }
        """
    },
]


async def run_test(test: dict, screenshot_dir: str = "tests/screenshots"):
    os.makedirs(screenshot_dir, exist_ok=True)
    name = test["name"]
    url = test["url"]
    print(f"\n{'='*50}")
    print(f"[{name}] 访问: {url}")

    async with AsyncCamoufox(
        headless=True,
        os="windows",
        block_webrtc=True,
    ) as browser:
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(4)  # 等待检测脚本执行完毕

            # 截图
            shot_path = f"{screenshot_dir}/{name}.png"
            await page.screenshot(path=shot_path, full_page=True)
            print(f"[{name}] 截图: {shot_path}")

            # 提取结果
            result = await page.evaluate(test["extract"])
            print(f"[{name}] 结果:")
            if isinstance(result, dict):
                for k, v in list(result.items())[:20]:  # 最多显示20项
                    status = v.get('status', v) if isinstance(v, dict) else v
                    val = v.get('value', '') if isinstance(v, dict) else ''
                    flag = '✓' if status == 'PASS' else ('✗' if status == 'FAIL' else ' ')
                    print(f"  {flag} {k}: {val or status}")
            else:
                print(f"  {str(result)[:300]}")

        except Exception as e:
            print(f"[{name}] 错误: {e}")


async def main():
    print("开始反检测效果测试...")
    print(f"代理: 无（直连）")
    # 只测sannysoft，最直观
    await run_test(TESTS[0])
    print("\n" + "="*50)
    print("测试完成，截图保存在 tests/screenshots/")


if __name__ == "__main__":
    asyncio.run(main())
