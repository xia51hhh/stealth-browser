"""
指纹检测测试 - 访问公开检测站点，验证反检测效果
运行: python -m pytest tests/test_fingerprint.py -s
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.browser import StealthBrowser


TEST_SITES = [
    ("Sannysoft",     "https://bot.sannysoft.com"),
    ("Browserleaks",  "https://browserleaks.com/javascript"),
    ("Creepjs",       "https://abrahamjuliot.github.io/creepjs/"),
]


async def run_check(url: str, name: str, out_dir: str = "tests/screenshots"):
    os.makedirs(out_dir, exist_ok=True)
    async with StealthBrowser() as sb:
        page = await sb.new_page()
        print(f"\n[{name}] 访问 {url} ...")
        await page.stealth_goto(url)
        await asyncio.sleep(4)   # 等待检测脚本运行完毕
        path = f"{out_dir}/{name.lower()}.png"
        await page.save_screenshot(path)
        print(f"[{name}] 截图已保存: {path}")


async def main():
    for name, url in TEST_SITES:
        await run_check(url, name)


if __name__ == "__main__":
    asyncio.run(main())
