"""
代理池测试 - 扫描本地代理端口，验证轮换和重试功能
运行: python tests/test_proxy_pool.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from proxy.pool import LocalProxyPool, with_proxy_retry
from curl_cffi.requests import AsyncSession


async def test_scan():
    print("=== 1. 扫描代理端口 ===")
    pool = LocalProxyPool(host='192.168.31.30', port_range=(10000, 10010))
    await pool.init()
    print(pool.stats())
    print()
    return pool


async def test_rotation(pool: LocalProxyPool):
    print("=== 2. 轮换测试（连续获取5次）===")
    seen = []
    for i in range(5):
        proxy = pool.get()
        seen.append(proxy)
        print(f"  [{i+1}] {proxy}")
    print()


async def test_retry(pool: LocalProxyPool):
    print("=== 3. 带重试的HTTP请求 ===")

    async def fetch(proxy_url):
        async with AsyncSession(
            impersonate="chrome120",
            proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None,
            timeout=10,
        ) as session:
            resp = await session.get("https://httpbin.org/ip")
            ip = resp.json().get("origin", "?")
            print(f"  出口IP: {ip} (via {proxy_url})")
            return ip

    for i in range(3):
        try:
            await with_proxy_retry(pool, fetch, max_retries=3)
        except Exception as e:
            print(f"  失败: {e}")
    print()


async def test_with_camoufox(pool: LocalProxyPool):
    print("=== 4. 与Camoufox集成测试 ===")
    import glob
    from camoufox.async_api import AsyncCamoufox

    proxy_cfg = pool.get_proxy_dict()
    print(f"  使用代理: {proxy_cfg}")

    async with AsyncCamoufox(
        headless=True,
        os='windows',
        block_webrtc=True,
        proxy=proxy_cfg,
    ) as browser:
        page = await browser.new_page()
        await page.goto('https://httpbin.org/ip', timeout=20000)
        ip = await page.evaluate("() => document.body.innerText")
        print(f"  浏览器出口IP: {ip[:80]}")
    print()


async def main():
    pool = await test_scan()
    await test_rotation(pool)
    await test_retry(pool)
    await test_with_camoufox(pool)
    print("=== 所有测试完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
