"""快速测试 - 只测 bot.sannysoft.com 验证基本功能"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import StealthBrowser


async def quick_test():
    print("启动隐身浏览器...")
    async with StealthBrowser() as browser:
        page = await browser.new_page()

        # 测试1: SannySoft
        print("[1/2] 访问 bot.sannysoft.com ...")
        await page.stealth_goto("https://bot.sannysoft.com/")
        await asyncio.sleep(3)
        await page.human.human_scroll("down", 300)
        await asyncio.sleep(1)
        f1 = f"screenshots/sannysoft_{int(time.time())}.png"
        await page.page.screenshot(path=f1, full_page=True)
        print(f"  截图: {f1}")

        # 测试2: Incolumitas
        print("[2/2] 访问 bot.incolumitas.com ...")
        await page.stealth_goto("https://bot.incolumitas.com/")
        await asyncio.sleep(8)
        await page.human.random_mouse_movement(count=5)
        await page.human.human_scroll("down", 500)
        await asyncio.sleep(2)
        f2 = f"screenshots/incolumitas_{int(time.time())}.png"
        await page.page.screenshot(path=f2, full_page=True)
        print(f"  截图: {f2}")

        print("\n完成! 请查看 screenshots/ 目录")


if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    asyncio.run(quick_test())
