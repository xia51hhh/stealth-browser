"""
反检测测试套件
自动访问多个检测网站并截图保存结果
"""
import asyncio
import os
import sys
import time

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import StealthBrowser


# 检测网站列表（优先级从高到低）
DETECTION_SITES = [
    {
        "name": "SannySoft Bot Detection",
        "url": "https://bot.sannysoft.com/",
        "wait": 3,
        "priority": "P0",
        "desc": "基础自动化检测（webdriver、chrome对象、权限等）",
    },
    {
        "name": "Incolumitas BotOrNot",
        "url": "https://bot.incolumitas.com/",
        "wait": 8,
        "priority": "P0",
        "desc": "综合 bot 检测，包含行为分析",
    },
    {
        "name": "BrowserLeaks WebRTC",
        "url": "https://browserleaks.com/webrtc",
        "wait": 5,
        "priority": "P0",
        "desc": "WebRTC IP 泄漏检测",
    },
    {
        "name": "BrowserLeaks Canvas",
        "url": "https://browserleaks.com/canvas",
        "wait": 5,
        "priority": "P1",
        "desc": "Canvas 指纹检测",
    },
    {
        "name": "BrowserLeaks JavaScript",
        "url": "https://browserleaks.com/javascript",
        "wait": 5,
        "priority": "P1",
        "desc": "JavaScript 环境检测",
    },
    {
        "name": "CreepJS",
        "url": "https://abrahamjuliot.github.io/creepjs/",
        "wait": 15,
        "priority": "P1",
        "desc": "最严格的指纹检测（需要较长加载时间）",
    },
    {
        "name": "PixelScan",
        "url": "https://pixelscan.net/",
        "wait": 8,
        "priority": "P1",
        "desc": "综合浏览器指纹一致性检测",
    },
]


async def run_detection_tests():
    """运行所有检测测试"""
    os.makedirs("screenshots", exist_ok=True)

    print("=" * 60)
    print("  反检测测试套件 - Stealth Browser Framework")
    print("=" * 60)

    async with StealthBrowser() as browser:
        page = await browser.new_page()

        results = []
        for i, site in enumerate(DETECTION_SITES, 1):
            print(f"\n[{i}/{len(DETECTION_SITES)}] {site['priority']} "
                  f"测试: {site['name']}")
            print(f"  URL: {site['url']}")
            print(f"  说明: {site['desc']}")

            try:
                await page.stealth_goto(site["url"], wait_until="domcontentloaded")
                # 等待页面检测完成
                print(f"  等待 {site['wait']}s 让检测完成...")
                await asyncio.sleep(site["wait"])

                # 模拟一些人类行为
                await page.human.random_mouse_movement(count=3)
                await page.human.human_scroll("down", 200)
                await asyncio.sleep(1)

                # 截图
                filename = f"screenshots/{site['name'].replace(' ', '_')}_{int(time.time())}.png"
                await page.page.screenshot(path=filename, full_page=True)
                print(f"  截图保存: {filename}")
                results.append({"site": site["name"], "status": "OK", "file": filename})

            except Exception as e:
                print(f"  错误: {e}")
                results.append({"site": site["name"], "status": f"FAIL: {e}"})

        print("\n" + "=" * 60)
        print("  测试结果汇总")
        print("=" * 60)
        for r in results:
            status = "PASS" if r["status"] == "OK" else "FAIL"
            print(f"  [{status}] {r['site']}")
            if "file" in r:
                print(f"         -> {r['file']}")
        print("=" * 60)
        print("\n请检查 screenshots/ 目录中的截图来评估检测结果。")


if __name__ == "__main__":
    asyncio.run(run_detection_tests())
