#!/usr/bin/env python3
"""
Stealth Browser - 反检测浏览器自动化框架
基于 Patchright (Playwright 反检测分支)

用法:
    # 运行检测测试
    python run.py test

    # 交互式使用（打开浏览器等待操作）
    python run.py interactive

    # 运行自定义脚本
    python run.py script your_script.py
"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.browser import StealthBrowser


async def cmd_test():
    """运行反检测测试"""
    os.makedirs("screenshots", exist_ok=True)

    print("=" * 60)
    print("  Stealth Browser - 反检测验证")
    print("=" * 60)

    async with StealthBrowser() as browser:
        page = await browser.new_page()

        # --- 基础指纹 ---
        print("\n[1/3] 浏览器指纹检测...")
        await page.page.goto("https://example.com", timeout=30000)
        await asyncio.sleep(1)

        checks = {
            "navigator.webdriver": ("navigator.webdriver", lambda v: v is False),
            "window.chrome": ("!!window.chrome", lambda v: v is True),
            "plugins.length": ("navigator.plugins.length", lambda v: v > 0),
            "languages": ("JSON.stringify(navigator.languages)", lambda v: "zh" in str(v)),
            "userAgent": ("navigator.userAgent", lambda v: "Headless" not in str(v)),
        }
        for label, (js, check) in checks.items():
            val = await page.page.evaluate(js)
            ok = check(val)
            print(f"  [{'PASS' if ok else 'FAIL'}] {label} = {val}")

        # --- AreYouHeadless ---
        print("\n[2/3] AreYouHeadless 检测...")
        try:
            await page.stealth_goto("https://arh.antoinevastel.com/bots/areyouheadless")
            await asyncio.sleep(3)
            text = await page.page.evaluate("document.body?.innerText || ''")
            passed = "not" in text.lower() and "headless" in text.lower()
            print(f"  [{'PASS' if passed else 'FAIL'}] {text.split(chr(10))[3] if len(text.split(chr(10))) > 3 else text[:80]}")
            await page.page.screenshot(path="screenshots/test_headless.png")
        except Exception as e:
            print(f"  [SKIP] {e}")

        # --- Detect Headless ---
        print("\n[3/3] Detect-Headless 检测 (16项)...")
        try:
            await page.stealth_goto(
                "https://infosimples.github.io/detect-headless/",
                timeout=30000
            )
            await asyncio.sleep(4)

            results = await page.page.evaluate("""
            () => {
                const rows = document.querySelectorAll('table tr');
                const data = [];
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const name = cells[0]?.innerText?.trim();
                        const result = cells[1]?.innerText?.trim();
                        const bg = getComputedStyle(cells[1]).backgroundColor || '';
                        // rgb(0, 128, 0) = green, rgb(0, 255, 0) = lime/bright green
                        const isRed = bg.includes('255, 0, 0') || bg.includes('red');
                        const isYellow = bg.includes('255, 255, 0') || bg.includes('yellow');
                        const pass = !isRed && !isYellow;
                        data.push({name, result: (result||'').substring(0,60), pass});
                    }
                });
                return data;
            }
            """)
            pass_c = sum(1 for r in results if r["pass"])
            fail_c = len(results) - pass_c
            for r in results:
                print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['name']}: {r['result']}")

            await page.page.screenshot(path="screenshots/test_detect.png", full_page=True)
            print(f"\n  总计: {pass_c}/{len(results)} 通过")
        except Exception as e:
            print(f"  [SKIP] {e}")

    print("\n" + "=" * 60)
    print("  测试完成! 截图在 screenshots/ 目录")
    print("=" * 60)


async def cmd_interactive():
    """交互模式 - 打开浏览器保持运行"""
    print("启动隐身浏览器（交互模式）...")
    print("浏览器将在 VNC 中打开，手动操作完成后按 Ctrl+C 退出\n")

    browser = StealthBrowser()
    await browser.launch()
    page = await browser.new_page()
    await page.stealth_goto("https://www.google.com")
    print("浏览器已打开 google.com")
    print("按 Ctrl+C 关闭...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await browser.close()
        print("浏览器已关闭")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "test":
        asyncio.run(cmd_test())
    elif cmd == "interactive":
        asyncio.run(cmd_interactive())
    elif cmd == "script":
        if len(sys.argv) < 3:
            print("用法: python run.py script <script_path>")
            return
        # 执行用户脚本，注入 StealthBrowser 到全局
        script_path = sys.argv[2]
        with open(script_path) as f:
            code = f.read()
        exec(code, {"StealthBrowser": StealthBrowser, "asyncio": asyncio})
    else:
        print(f"未知命令: {cmd}")
        print("可用: test | interactive | script <path>")


if __name__ == "__main__":
    main()
