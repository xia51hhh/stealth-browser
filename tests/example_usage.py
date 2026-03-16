"""
使用示例 - 展示框架的基本用法
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import StealthBrowser


async def example_basic():
    """基础用法 - 访问网页并截图"""
    async with StealthBrowser() as browser:
        page = await browser.new_page()

        # 隐身导航（自动做随机鼠标移动）
        await page.stealth_goto("https://www.google.com")

        # 人类式输入搜索
        await page.stealth_type('textarea[name="q"]', "Patchright github")
        await page.human.random_delay()

        # 人类式按回车
        await page.page.keyboard.press("Enter")
        await page.page.wait_for_load_state("domcontentloaded")

        # 等待并滚动查看结果
        await page.human.random_delay(1000, 2000)
        await page.stealth_scroll("down", 300)

        # 截图
        await page.save_screenshot("screenshots/google_search.png")
        print("搜索完成，截图已保存")


async def example_with_proxy():
    """带代理的用法 - 修改配置文件中的 proxy 部分即可"""
    # 也可以直接修改配置
    async with StealthBrowser() as browser:
        page = await browser.new_page()
        await page.stealth_goto("https://httpbin.org/ip")
        content = await page.page.content()
        print(f"当前 IP: {content}")


async def example_multi_page():
    """多标签页示例"""
    async with StealthBrowser() as browser:
        # 打开多个页面
        page1 = await browser.new_page()
        page2 = await browser.new_page()

        await page1.stealth_goto("https://example.com")
        await page2.stealth_goto("https://httpbin.org/headers")

        title1 = await page1.page.title()
        title2 = await page2.page.title()
        print(f"页面1: {title1}")
        print(f"页面2: {title2}")


if __name__ == "__main__":
    print("运行基础示例...")
    asyncio.run(example_basic())
