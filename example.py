"""
快速使用示例 - 演示完整的反检测浏览器用法
运行: python example.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.browser import StealthBrowser
from core.http_client import StealthHTTPClient
from proxy.pool import ProxyPool


# ── 示例1：浏览器访问（需要JS渲染的页面）────────────────────────────
async def example_browser():
    async with StealthBrowser() as sb:
        page = await sb.new_page()

        # 访问检测站点，验证反检测效果
        await page.stealth_goto("https://bot.sannysoft.com")
        await asyncio.sleep(3)
        await page.save_screenshot("screenshots/sannysoft.png")
        print("[浏览器] 截图已保存")

        # 人类化交互示例
        await page.stealth_goto("https://www.example.com")
        await page.stealth_scroll("down", 400)
        # await page.stealth_type("input[name='q']", "hello world")
        # await page.stealth_click("button[type='submit']")


# ── 示例2：纯HTTP请求（不需要JS，速度更快）──────────────────────────
async def example_http():
    async with StealthHTTPClient(impersonate="chrome120") as client:
        resp = await client.get("https://httpbin.org/headers")
        print("[HTTP] 状态码:", resp.status_code)
        print("[HTTP] 响应头:", resp.json())


# ── 示例3：带代理轮换的浏览器 ──────────────────────────────────────
async def example_with_proxy():
    # 从文件加载代理列表（每行一个）
    # pool = ProxyPool.from_file("proxies.txt")

    # 或直接传入列表
    pool = ProxyPool.from_list([
        # "http://user:pass@1.2.3.4:8080",
        # "socks5://5.6.7.8:1080",
    ])

    proxy = pool.get()  # None = 直连
    print(f"[代理] 使用: {proxy or '直连'}")
    print(f"[代理] 池状态: {pool.stats()}")

    async with StealthBrowser() as sb:
        # 代理在 config/default.yaml 中配置
        # 或在此处动态传入（需修改 StealthBrowser 支持运行时代理）
        page = await sb.new_page()
        await page.stealth_goto("https://httpbin.org/ip")
        content = await page.page.content()
        print("[代理] 页面内容片段:", content[:200])


if __name__ == "__main__":
    print("选择示例:")
    print("  1 - 浏览器访问 + 截图")
    print("  2 - 纯HTTP请求（curl_cffi）")
    print("  3 - 代理池演示")
    choice = input("输入编号 [1/2/3]: ").strip()

    if choice == "1":
        asyncio.run(example_browser())
    elif choice == "2":
        asyncio.run(example_http())
    elif choice == "3":
        asyncio.run(example_with_proxy())
    else:
        print("无效选择")
